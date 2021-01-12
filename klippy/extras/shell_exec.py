# Add ability to define custom g-code shell scripts
#
# Copyright (C) 2018-2019  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import os, shlex, subprocess, traceback, logging, ast, jinja2, getpass, stat

######################################################################
# Template handling
######################################################################

try:  # py3
    from shlex import quote as shlex_quote
except ImportError:  # py2
    from pipes import quote as shlex_quote

def cmd_quote(input):
    #safe shell quoting so params are not evaluated as seperate commands
    return shlex_quote(input)

class ShellCommand:
    def __init__(self, printer, cmd):
        self.printer = printer
        self.name = cmd
        self.gcode = self.printer.lookup_object('gcode')
        self.output_cb = self.gcode.respond_info
        cmd = os.path.expanduser(cmd)
        self.command = shlex.split(cmd)
        self.proc_fd = None
        self.partial_output = ""

    def _process_output(self, eventime):
        if self.proc_fd is None:
            return
        try:
            data = os.read(self.proc_fd, 4096)
        except Exception:
            pass
        data = self.partial_output + data
        if '\n' not in data:
            self.partial_output = data
            return
        elif data[-1] != '\n':
            split = data.rfind('\n') + 1
            self.partial_output = data[split:]
            data = data[:split]
        try:
            self.output_cb(data)
        except Exception:
            logging.exception("Error writing command output")

    def set_output_callback(self, cb=None):
        if cb is None:
            self.output_cb = self.gcode.respond_info
        else:
            self.output_cb = cb

    def run(self, timeout=2., verbose=True):
        if not timeout:
            # Fire and forget commands cannot be verbose as we can't
            # clean up after the process terminates
            verbose = False
        reactor = self.printer.get_reactor()
        try:
            proc = subprocess.Popen(
                self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except Exception:
            logging.exception(
                "shell_command: Command {%s} failed" % (self.name))
            raise self.gcode.error("Error running command {%s}" % (self.name))
        if verbose:
            self.proc_fd = proc.stdout.fileno()
            self.gcode.respond_info("Running Command {%s}...:" % (self.name))
            hdl = reactor.register_fd(self.proc_fd, self._process_output)
        elif not timeout:
            # fire and forget, return from execution
            return
        eventtime = reactor.monotonic()
        endtime = eventtime + timeout
        complete = False
        while eventtime < endtime:
            eventtime = reactor.pause(eventtime + .05)
            if proc.poll() is not None:
                complete = True
                break
        if not complete:
            proc.terminate()
        if verbose:
            if self.partial_output:
                self.output_cb(self.partial_output)
                self.partial_output = ""
            if complete:
                msg = "Command {%s} finished\n" % (self.name)
            else:
                msg = "Command {%s} timed out" % (self.name)
            self.gcode.respond_info(msg)
            reactor.unregister_fd(hdl)
            self.proc_fd = None

# Wrapper for access to printer object get_status() methods
class GetStatusWrapper:
    def __init__(self, printer, eventtime=None):
        self.printer = printer
        self.eventtime = eventtime
        self.cache = {}
    def __getitem__(self, val):
        sval = str(val).strip()
        if sval in self.cache:
            return self.cache[sval]
        po = self.printer.lookup_object(sval, None)
        if po is None or not hasattr(po, 'get_status'):
            raise KeyError(val)
        if self.eventtime is None:
            self.eventtime = self.printer.get_reactor().monotonic()
        self.cache[sval] = res = dict(po.get_status(self.eventtime))
        return res
    def __contains__(self, val):
        try:
            self.__getitem__(val)
        except KeyError as e:
            return False
        return True
    def __iter__(self):
        for name, obj in self.printer.lookup_objects():
            if self.__contains__(name):
                yield name

# Wrapper around a Jinja2 template
class TemplateWrapper:
    def __init__(self, printer, env, name, script, timeout, verbose):
        self.printer = printer
        self.name = name
        self.timeout = timeout
        self.verbose = verbose
        self.gcode = self.printer.lookup_object('gcode')
        shell_exec = self.printer.lookup_object('shell_exec')
        self.create_template_context = shell_exec.create_template_context
        try:
            self.template = env.from_string(script)
        except Exception as e:
            msg = "Error loading template '%s': %s" % (
                 name, traceback.format_exception_only(type(e), e)[-1])
            logging.exception(msg)
            raise printer.config_error(msg)
    def render(self, context=None):
        if context is None:
            context = self.create_template_context()
        try:
            return str(self.template.render(context))
        except Exception as e:
            msg = "Error evaluating '%s': %s" % (
                self.name, traceback.format_exception_only(type(e), e)[-1])
            logging.exception(msg)
            raise self.gcode.error(msg)
    def run_command(self, context=None):
        cmd = ShellCommand(self.printer, self.render(context))
        cmd.run(self.timeout, self.verbose)

# Main gcode shell script template tracking
class PrinterShellExec:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.env = jinja2.Environment('{%', '%}', '{', '}')
        self.env.filters['quote'] = cmd_quote
        self.verbose = config.getboolean("verbose", True)
        self.timeout = config.getint("timeout", 2)
    def load_template(self, config, option, default=None):
        name = "%s:%s" % (config.get_name(), option)
        if default is None:
            script = config.get(option)
        else:
            script = config.get(option, default)
        return TemplateWrapper(self.printer, self.env, name, script, self.timeout, self.verbose)
    def _action_emergency_stop(self, msg="action_emergency_stop"):
        self.printer.invoke_shutdown("Shutdown due to %s" % (msg,))
        return ""
    def _action_respond_info(self, msg):
        self.printer.lookup_object('gcode').respond_info(msg)
        return ""
    def _action_raise_error(self, msg):
        raise self.printer.command_error(msg)
    def _action_call_remote_method(self, method, **kwargs):
        webhooks = self.printer.lookup_object('webhooks')
        try:
            webhooks.call_remote_method(method, **kwargs)
        except self.printer.command_error:
            logging.exception("Remote Call Error")
        return ""
    def create_template_context(self, eventtime=None):
        return {
            'printer': GetStatusWrapper(self.printer, eventtime),
            'action_emergency_stop': self._action_emergency_stop,
            'action_respond_info': self._action_respond_info,
            'action_raise_error': self._action_raise_error,
            'action_call_remote_method': self._action_call_remote_method,
        }

def load_config(config):
    return PrinterShellExec(config)


######################################################################
# Shell Exec
######################################################################

class ShellExec:
    def __init__(self, config):
        name = config.get_name().split()[1]
        self.alias = name.upper()
        self.printer = printer = config.get_printer()
        shell_exec = printer.load_object(config, 'shell_exec')
        self.template = shell_exec.load_template(config, 'command')
        self.gcode = printer.lookup_object('gcode')
        self.rename_existing = config.get("rename_existing", None)
        self.verbose = config.getboolean("verbose", True)
        self.timeout = config.getint("timeout", 2)
        self.check_file_permissions(printer.lookup_object('configfile').get_config_file_names())
        if self.rename_existing is not None:
            if (self.gcode.is_traditional_gcode(self.alias)
                != self.gcode.is_traditional_gcode(self.rename_existing)):
                raise config.error(
                    "Shell command rename of different types ('%s' vs '%s')"
                    % (self.alias, self.rename_existing))
            printer.register_event_handler("klippy:connect",
                                           self.handle_connect)
        else:
            self.gcode.register_command(self.alias, self.cmd,
                                        desc=self.cmd_desc)
        self.gcode.register_mux_command("SET_COMMAND_VARIABLE", "COMMAND",
                                        name, self.cmd_SET_COMMAND_VARIABLE,
                                        desc=self.cmd_SET_COMMAND_VARIABLE_help)
        self.in_script = False
        prefix = 'default_parameter_'
        self.kwparams = { o[len(prefix):].upper(): config.get(o)
                          for o in config.get_prefix_options(prefix) }
        self.variables = {}
        prefix = 'variable_'
        for option in config.get_prefix_options(prefix):
            try:
                self.variables[option[len(prefix):]] = ast.literal_eval(
                    config.get(option))
            except ValueError as e:
                raise config.error(
                    "Option '%s' in section '%s' is not a valid literal" % (
                        option, config.get_name()))

    def check_file_permissions(self, files):
        uid = os.geteuid()
        gid = os.getegid()
        for filename in files:
            stat_info = os.stat(filename)
            if stat_info.st_uid != uid:
                uname = getpass.getuser()
                raise self.printer.config_error(
                    "Config file %s not owned by current klipper user: %s"
                    % (filename, uname))

            if stat_info.st_gid != gid:
                gname = getpass.getuser()
                raise self.printer.config_error(
                    "Config file %s, not owned by current klipper group: %s"
                    % (filename, gname))

            if bool(stat_info.st_mode & stat.S_IWOTH):
                raise self.printer.config_error(
                    "Config file %s, can be written to by others.  \nEx fix: sudo chmod 644 %s"
                    % (filename, filename,))

            if bool(stat_info.st_mode & stat.S_IWGRP):
                raise self.printer.config_error(
                    "Config file %s, can be written to by group.  \nEx fix: sudo chmod 644 %s"
                    % (filename, filename,))

    def handle_connect(self):
        prev_cmd = self.gcode.register_command(self.alias, None)
        if prev_cmd is None:
            raise self.printer.config_error(
                "Existing command '%s' not found in shell_exec rename"
                % (self.alias,))
        pdesc = "Renamed builtin of '%s'" % (self.alias,)
        self.gcode.register_command(self.rename_existing, prev_cmd, desc=pdesc)
        self.gcode.register_command(self.alias, self.cmd, desc=self.cmd_desc)
        return dict(self.variables)
    def get_status(self, eventtime):
        return dict(self.variables)
    cmd_SET_COMMAND_VARIABLE_help = "Set the value of a G-Code shell script variable"
    def cmd_SET_COMMAND_VARIABLE(self, gcmd):
        variable = gcmd.get('VARIABLE')
        value = gcmd.get('VALUE')
        if variable not in self.variables:
            if variable in self.kwparams:
                self.kwparams[variable] = value
                return
            raise gcmd.error("Unknown shell_exec variable '%s'" % (variable,))
        try:
            literal = ast.literal_eval(value)
        except ValueError as e:
            raise gcmd.error("Unable to parse '%s' as a literal" % (value,))
        self.variables[variable] = literal
    cmd_desc = "G-Code shell command"
    def cmd(self, gcmd):
        params = gcmd.get_command_parameters()
        kwparams = dict(self.kwparams)
        kwparams.update(params)
        kwparams.update(self.variables)
        kwparams.update(self.template.create_template_context())
        kwparams['params'] = params
        self.in_script = True
        try:
            self.template.run_command(kwparams)
        finally:
            self.in_script = False

def load_config_prefix(config):
    return ShellExec(config)

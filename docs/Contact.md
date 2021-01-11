This document provides contact information for Klipper.

1. [I have a question about Klipper](#i-have-a-question-about-klipper)
2. [I have a feature request](#i-have-a-feature-request)
3. [Help! It doesn't work!](#help-it-doesnt-work)
4. [I found a bug in Klipper](#i-found-a-bug-in-klipper)
5. [I am making changes that I'd like to include in Klipper](#i-am-making-changes-that-id-like-to-include-in-klipper)
6. [Klipper IRC channel](#irc)
7. [Klipper mailing list](#mailing-list)

I have a question about Klipper
===============================

Many questions we receive are general 3d-printing questions that are
not specific to Klipper. If you have a general question or are
experiencing general printing problems, then you will likely get a
faster response by joining a general 3d-printing forum and asking
there.

If you have a question specific to Klipper then you can join the
[Klipper IRC channel](#irc) and ask there.

Do not open a github issue to ask a question.

I have a feature request
========================

All new features require someone interested and able to implement that
feature. You can ask if someone is working on a feature (or is
interested in working on it) in the [Klipper IRC channel](#irc).

Unfortunately, if no one is currently working on a feature, then it is
unlikely to be implemented in the near future. We only track features
that are under active development.

Do not open a github issue to request a feature.

Help! It doesn't work!
======================

The majority of problem reports we see are eventually tracked down to:
1. Subtle errors in the hardware, or
2. Skipping steps described in Klipper's installation and
   configuration documentation.

If you are experiencing problems we recommend carefully reading the
[Klipper documentation](Overview.md) and following the instructions
provided there.

If the problem seems mechanical in nature, then we recommend carefully
inspecting the printer hardware (all joints, wires, screws, etc.) and
verifying nothing is abnormal. For mechanical issues you will likely
get a faster response by joining a general 3d-printing forum and
asking about it there.

If you think the issue may be related to Klipper then you can join the
[Klipper IRC channel](#irc) and ask there.

Do not open a github issue to request help.

I found a bug in Klipper
========================

Klipper is an open-source project and we appreciate it when
collaborators provide bug reports.

There is important information that will be needed in order to fix a
bug. Please follow these steps:
1. If unsure if there is a problem then you can ask first on the
   [Klipper IRC channel](#irc). Do not open a github issue if unsure.
2. Make sure you are running unmodified code from
   [https://github.com/KevinOConnor/klipper](https://github.com/KevinOConnor/klipper)
   . If the code has been modified in any way or is obtained from any
   other source, then you will need to reproduce the problem on the
   pristine unmodified code from
   [https://github.com/KevinOConnor/klipper](https://github.com/KevinOConnor/klipper)
   prior to reporting an issue.
3. If possible, run an `M112` command in the OctoPrint terminal window
   immediately after the undesirable event occurs. This causes Klipper
   to go into a "shutdown state" and it will cause additional
   debugging information to be written to the log file.
4. Obtain the Klipper log file from the event. The log file has been
   engineered to answer common questions the Klipper developers have
   about the software and its environment (software version, hardware
   type, configuration, event timing, and hundreds of other
   questions).
   1. The Klipper log file is located in `/tmp/klippy.log` on the
      Klipper "host" computer (the Raspberry Pi).
   2. An "scp" or "sftp" utility is needed to copy this log file to
      your desktop computer. The "scp" utility comes standard with
      Linux and MacOS desktops. There are freely available scp
      utilities for other desktops (eg, WinSCP). If using a graphical
      scp utility that can not directly copy `/tmp/klippy.log` then
      click on `..` or `parent folder` until you get to the root
      directory, click on the `tmp` folder, and then select the
      `klippy.log` file.
   3. Copy the log file to your desktop so that it can be attached to
      an issue report.
   4. Do not modify the log file in any way; do not provide a snippet
      of the log. Only the full unmodified log file provides the
      necessary information.
   5. If the log file is very large (eg, greater than 2MB) then one
      may need to compress the log with zip or gzip.
5. Open a github issue ticket at
   [https://github.com/KevinOConnor/klipper/issues](https://github.com/KevinOConnor/klipper/issues)
   and provide a clear description of the problem. The Klipper
   developers need to understand what steps were taken, what action
   was desired, and what action actually occurred. The Klipper log
   file **must be attached** to that ticket:
   ![attach-issue](img/attach-issue.png)

I am making changes that I'd like to include in Klipper
=======================================================

Klipper is open-source software and we appreciate new contributions.

New contributions (for both code and documentation) are submitted via
Github Pull Requests. See the
[CONTRIBUTING.md document](CONTRIBUTING.md) for important information.

There are several
[documents for developers](Overview.md#developer-documentation). If
you have questions on the code then you can ask on the
[Klipper IRC channel](#irc). If you would like to provide feedback on
current progress then you can open a Github Pull Request with your
current code along with a description of your results.

IRC
===

One may join the #klipper channel on freenode.net
(`irc://chat.freenode.net:6667`).

To communicate in this IRC channel one will need an IRC client.
Configure it to connect to chat.freenode.net on port 6667 and join the
`#klipper` channel (`/join #klipper`).

If asking a question on IRC, be sure to ask the question and then stay
connected to the channel to receive responses. Due to timezone
differences, it may take several hours before receiving a response.

Mailing list
============

There is a mailing list for general discussions on Klipper. In order
to send an email to the list, one must first subscribe:
[https://www.freelists.org/list/klipper](https://www.freelists.org/list/klipper)
. Once subscribed, emails may be sent to `klipper@freelists.org`.

Archives of the mailing list are available at:
[https://www.freelists.org/archive/klipper/](https://www.freelists.org/archive/klipper/)

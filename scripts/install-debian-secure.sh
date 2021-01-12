#!/bin/bash
# This script installs Klipper on an debian
#

SYSTEMDDIR="/etc/systemd/system"
PYTHONDIR="/var/lib/klipper"
ETCDIR="/etc/klipper"
LOGDIR="/var/log/klipper"
SOCKETDIR="/var/run/klipper"
SDCARDDIR="/sdcard"
KLIPPER_USER='klipper'
KLIPPER_GROUP="$KLIPPER_USER"



# Step 1: Install system packages
install_packages()
{
    # Packages for python cffi
    PKGLIST="python-virtualenv virtualenv python-dev libffi-dev build-essential"
    # kconfig requirements
    PKGLIST="${PKGLIST} libncurses-dev"
    # hub-ctrl
    PKGLIST="${PKGLIST} libusb-dev"
    # AVR chip installation and building
    PKGLIST="${PKGLIST} avrdude gcc-avr binutils-avr avr-libc"
    # ARM chip installation and building
    PKGLIST="${PKGLIST} stm32flash libnewlib-arm-none-eabi"
    PKGLIST="${PKGLIST} gcc-arm-none-eabi binutils-arm-none-eabi libusb-1.0"

    # Update system package info
    report_status "Running apt-get update..."
    sudo apt-get update

    # Install desired packages
    report_status "Installing packages..."
    sudo apt-get install --yes ${PKGLIST}
}

# Step 1.5 create klipper user/group
create_users_dirs()
{
    if ! id "$KLIPPER_USER" &>/dev/null; then
        report_status "Creating Klipper User: $KLIPPER_USER"
        sudo useradd -r $KLIPPER_USER
        sudo usermod -a -G dialout $KLIPPER_USER #lets klipper talk to the printer
        sudo usermod -a -G $KLIPPER_GROUP pi #lets pi user view logs and add files to sdcard
    fi
}

# Step 2: Create python virtual environment
create_virtualenv()
{
    if [ ! -f ${PYTHONDIR}/bin/python ] ; then
        sudo mkdir -p ${PYTHONDIR}
        sudo chown $KLIPPER_USER:$KLIPPER_USER ${PYTHONDIR}
        sudo chmod 755 ${PYTHONDIR}
        sudo -u $KLIPPER_USER virtualenv -p python2 ${PYTHONDIR}
    fi

    report_status "Updating python virtual environment..."
    # Install/update dependencies
    sudo -u $KLIPPER_USER ${PYTHONDIR}/bin/pip install -r ${SRCDIR}/scripts/klippy-requirements.txt
}

# Step 3: Install startup script
install_script()
{
    # Create systemd service file
    report_status "Installing system start script..."
    sudo /bin/sh -c "cat > $SYSTEMDDIR/klipper.service" << EOF
#Systemd service file for klipper
[Unit]
Description=Starts klipper on startup
After=network.target

[Install]
WantedBy=multi-user.target

[Service]
Type=simple
User=$KLIPPER_USER
Group=$KLIPPER_GROUP
ExecStartPre=+/bin/mkdir -p "$SDCARDDIR"
ExecStartPre=+/bin/chown $KLIPPER_USER:$KLIPPER_GROUP "$SDCARDDIR"
ExecStartPre=+/bin/chmod 775 "$SDCARDDIR"
ExecStart=/usr/bin/env "\${STATE_DIRECTORY}/bin/python" ${SRCDIR}/klippy/klippy.py \${CONFIGURATION_DIRECTORY}/printer.cfg -l \${LOGS_DIRECTORY}/klippy.log -a \${RUNTIME_DIRECTORY}/uds -I \${RUNTIME_DIRECTORY}/printer
Restart=always
RestartSec=10
RuntimeDirectory=klipper
LogsDirectory=klipper
StateDirectory=klipper
ConfigurationDirectory=klipper
EOF
    # Use systemctl to enable the klipper systemd service script
    sudo systemctl enable klipper.service
}

# Step 4: Start host software
start_software()
{
    report_status "Launching Klipper host software... the first start could take a while for python to download dependencies."
    sudo systemctl start klipper
}

# Helper functions
report_status()
{
    echo -e "\n\n###### $1"
}

verify_ready()
{
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

# Step 5 create klipper user/group
sumarize_users_dirs()
{
    echo "Important information! "
    echo "Klipper User/Group: $KLIPPER_USER"

    echo "Service Unit File Location: $SYSTEMDDIR/klipper.service"

    echo "Klipper Config Dir: $ETCDIR"
    echo "Recomended permission and ownership of: $ETCDIR/print.cfg"
    echo "    chown $KLIPPER_USER:$KLIPPER_GROUP $ETCDIR/printer.cfg"
    echo "    chmod 644 $ETCDIR/printer.cfg"

    echo "Log dir:  $LOGDIR"
    echo "    tail -f $LOGDIR/klippy.log"

    echo "Socket and tty dir:  $SOCKETDIR"
    echo "    Octiprint tty setup: $SOCKETDIR/printer"
    echo "    Moonraker [server] section: klippy_uds_address: $SOCKETDIR/uds"

    echo "SDcard dir:  $SDCARDDIR"
    echo "    Klipper Config:"
    echo "    [virtual_sdcard]"
    echo "    path: /sdcard"
}

# Force script to exit if an error occurs
set -e

# Find SRCDIR from the pathname of this script
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"

# Run installation steps defined above
verify_ready
install_packages
create_users_dirs
create_virtualenv
install_script
start_software
sumarize_users_dirs

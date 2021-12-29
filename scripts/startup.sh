#!/bin/bash

# This script kills any running instances of the hardwareControl_server, the scheduler
# client, and the GUI client, then relaunches them. It should be installed to crontab
# as a startup task.
# (TODO: Move these to be managed by systemd instead)

INSTALL_DIR=/home/pi/pisces-deploy

export PYTHONPATH=$INSTALL_DIR/shared

PY=python3
#Kill if already running
echo "Killing processes..."
pkill -INT -f hardwareControl_server.py
pkill -INT -f scheduler.py
pkill -INT -f gui.py

export DISPLAY=:0.0

sleep 1

echo "Restarting server"
#start the grpc server
$PY $INSTALL_DIR/bin/hardwareControl_server.py &

#launch the scheduler client task
sleep 5
echo "Restarting scheduler"
$PY $INSTALL_DIR/bin/scheduler.py &

sleep 1
echo "Restarting GUI"
$PY $INSTALL_DIR/bin/gui.py &


#!/bin/bash

# This script kills any running instances of the hardwareControl_server, the scheduler
# client, and the GUI client, then relaunches them. It should be installed to crontab
# as a startup task.
# (TODO: Move these to be managed by systemd instead)

#Kill if already running
echo "Killing processes..."
pkill -INT -f hardwareControl_server.py
pkill -INT -f scheduler.py
pkill -INT -f gui.py

sleep 1

echo "Restarting server"
#start the grpc server
python /home/pi/Repositories/pisces/hal/hardwareControl_server.py &

#launch the scheduler client task
sleep 5
echo "Restarting scheduler"
python /home/pi/Repositories/pisces/hal/scheduler.py &

sleep 1
echo "Restarting GUI"
python /home/pi/Repositories/pisces/hal/gui.py &


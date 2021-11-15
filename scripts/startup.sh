#!/bin/bash

#Kill if already running
echo "Killing processes..."
pkill -INT -f hardwareControl_server.py
pkill -INT -f scheduler.py

sleep 1

echo "Restarting server"
#start the grpc server
python /home/pi/Repositories/pisces/hal/hardwareControl_server.py &

#launch the scheduler client task
sleep 5
echo "Restarting scheduler"
python /home/pi/Repositories/pisces/hal/scheduler.py &


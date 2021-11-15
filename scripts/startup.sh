#!/bin/bash

#start the grpc server
python /home/pi/Repositories/pisces/hal/hardwareControl_server.py &

#launch the scheduler client task
sleep 1
python /home/pi/Repositories/pisces/hal/scheduler.py &


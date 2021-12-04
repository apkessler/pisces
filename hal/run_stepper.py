#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A script for running the stepper
#
#
import logging
import grpc
import time
import json
import argparse

from enum import Enum
import datetime as dt
import hardwareControl_pb2
import hardwareControl_pb2_grpc
from hardwareControl_client import HardwareControlClient


def ml_to_steps(ml):
    return 1000*ml


def main():
    parser = argparse.ArgumentParser(description='Run the pump for a given number of mL')
    parser.add_argument('volume_ml', type=int, help='The number of mL to dispense')

    args = parser.parse_args()

    with grpc.insecure_channel('localhost:50051') as channel:
        hwCntrl = HardwareControlClient(channel)
        logging.info("Turning off tank lights for pump")
        #Just manually disable the enable relay for tnk lights... this should be smarter.
        #Shh I am ashamed. This should really be handled on server side
        hwCntrl.setRelayState(5, False) #Tank Light 1
        hwCntrl.setRelayState(7, False) #Tank Light 2

        time.sleep(0.5)

        nsteps = ml_to_steps(args.volume_ml)
        logging.info(f"Sending request to step {nsteps} for {args.volume_ml} mL")
        hwCntrl.moveStepper(nsteps)

        time.sleep((0.01 * nsteps) + 2)

        #renable the lights
        logging.info("Reenabling lights")
        hwCntrl.setRelayState(5, True) #Tank Light 1
        hwCntrl.setRelayState(7, True) #Tank Light 2



if __name__ == '__main__':
    logging.basicConfig(
        filename='/home/pi/log/dispense.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().setLevel(logging.INFO)
    try:
        main()
    except KeyboardInterrupt:
        print("Ending program")

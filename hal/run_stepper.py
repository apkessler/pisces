#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A script for running the stepper
#
#
import logging
from tkinter import Label
import grpc
import time
import json
import argparse
import threading
from enum import Enum
import datetime as dt
import hardwareControl_pb2
import hardwareControl_pb2_grpc
from hardwareControl_client import HardwareControlClient

STEP_BATCH = 500

def ml_to_steps(ml):
    return 1000*ml


def dispense(hwCntrl, volume_ml, stop_event):
    """Blocking call to dispense a certain number of mL

    Parameters
    ----------
    hwCntrl : [type]
        HwCntrl stub
    volume_ml : [type]
        Volume to dispense
    """

    logging.info("Turning off tank lights for pump")
    #Just manually disable the enable relay for tnk lights... this should be smarter.
    #Shh I am ashamed. This should really be handled on server side
    hwCntrl.setRelayState(5, False) #Tank Light 1
    hwCntrl.setRelayState(7, False) #Tank Light 2

    time.sleep(0.5)

    total_nsteps = ml_to_steps(volume_ml)
    logging.info(f"Sending request to step {total_nsteps} for {volume_ml} mL")


    while total_nsteps > 0 and (not stop_event.is_set()):

        stepsThisTime = STEP_BATCH if total_nsteps > STEP_BATCH else total_nsteps

        hwCntrl.moveStepper(stepsThisTime)
        logging.info(f"Sending request to step {stepsThisTime}")
        #sleep for t = (nsteps*.01 + 2)sec in 0.1 sec intervals
        #Inner loop looks for stop events
        for i in range(int(stepsThisTime/10 + 5)):
            time.sleep(0.1)
            if stop_event.is_set():
                logging.info(f"Dispense got stop flag early!")
                break
        total_nsteps -= STEP_BATCH

    time.sleep(0.1)

    #renable the lights
    logging.info("Reenabling lights")
    hwCntrl.setRelayState(5, True) #Tank Light 1
    hwCntrl.setRelayState(7, True) #Tank Light 2



if __name__ == '__main__':
    logging.basicConfig(
        filename='dispense.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description='Run the pump for a given number of mL')
    parser.add_argument('volume_ml', type=int, help='The number of mL to dispense')

    args = parser.parse_args()

    stop_event = threading.Event()
    with grpc.insecure_channel('localhost:50051') as channel:
        hwCntrl = HardwareControlClient(channel)
        stopFlag = False
        t = threading.Thread(target=dispense, args=(hwCntrl, args.volume_ml, stop_event), daemon=True)
        t.start()

        try:
            while t.is_alive():
                time.sleep(0.1)
            logging.info("Dispense completed")
        except KeyboardInterrupt:
            logging.info("Got keyboard interrupt")
            stop_event.set()

        t.join()
        logging.info("Dispense thread closed")

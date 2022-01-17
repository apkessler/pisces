#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A script/library for running the fertilizer pump
# to dispense fertilzier
#
import logging
import grpc
import time
import argparse
import threading
import json
import os

from hwcontrol_client import HardwareControlClient

_jData = None

#Do this setup up here so we get config and logging even if function is imported on its own
with open(os.path.join(os.path.dirname(__file__), 'dispense.json'), 'r') as jsonfile:
    _jData = json.load(jsonfile)


def ml_to_steps(ml:int) -> int:
    """Convert from mL to number of stepper motor steps needed to dispense that volume.

    Parameters
    ----------
    ml : int
        Desired volume in mL

    Returns
    -------
    int
        Needed stepper motor steps
    """
    return _jData['steps_per_ml']*ml


def dispense(hwCntrl, volume_ml:int, stop_event:threading.Event):
    """Blocking call to dispense a certain number of mL

    Parameters
    ----------
    hwCntrl : [type]
        HwCntrl stub
    volume_ml : int
        Volume to dispense, in mL
    stop_event : Threading event
        When event is set, function will not send anymore dispense commands and exit
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

        stepsThisTime = _jData['steps_per_command'] if total_nsteps >  _jData['steps_per_command'] else total_nsteps

        hwCntrl.moveStepper(stepsThisTime)
        logging.info(f"Sending request to step {stepsThisTime}")
        #sleep for t = (nsteps*.01 + 2)sec in 0.1 sec intervals
        #Inner loop looks for stop events
        for i in range(int(stepsThisTime/10 + 5)):
            time.sleep(0.1)
            if stop_event.is_set():
                logging.info(f"Dispense got stop flag early!")
                break
        total_nsteps -= _jData['steps_per_command']

    logging.info("Not sending anymore dispense commands")
    time.sleep(6)#Allow some time for ongoing dispense to finish

    #renable the lights
    logging.info("Reenabling lights")
    hwCntrl.setRelayState(5, True) #Tank Light 1
    hwCntrl.setRelayState(7, True) #Tank Light 2



if __name__ == '__main__':
    logging.basicConfig(
    filename=_jData['log_name'],
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().setLevel(_jData['log_level'])


    parser = argparse.ArgumentParser(description='Run the pump for a given number of mL')
    parser.add_argument('volume_ml', nargs='?', type=int, default=_jData['default_volume_ml'], help='The number of mL to dispense')

    args = parser.parse_args()

    stop_event = threading.Event()
    with grpc.insecure_channel(_jData['server']) as channel:
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

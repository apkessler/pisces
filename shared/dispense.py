#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A script/library for running the fertilizer pump
# to dispense fertilzier
#

import grpc
import time
import argparse
import threading
import json
import os

from loguru import logger

from hwcontrol_client import HardwareControlClient

_jData = None

#Do this setup up here so we get config and logger even if function is imported on its own
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
        When event is set, function will send a STOP event to stepper controller and wait for stepper to report it did stop
    """

    logger.info("Turning off tank lights for pump")
    #Just manually disable the enable relay for tnk lights... this should be smarter.
    #Shh I am ashamed. This should really be handled on server side
    hwCntrl.setRelayState(5, False) #Tank Light 1
    hwCntrl.setRelayState(7, False) #Tank Light 2

    time.sleep(0.5)

    total_nsteps = ml_to_steps(volume_ml)
    logger.info(f"Sending request to step {total_nsteps} for {volume_ml} mL")

    logger.info(f"Sending request to step {total_nsteps}")
    hwCntrl.moveStepper(total_nsteps)

    while hwCntrl.getIsStepperActive():

        if (stop_event.is_set()):
            logger.info(f"Dispense got stop flag early!")
            hwCntrl.stopStepper()
            stop_event.clear() #So this doesn't keep retriggering, but we'll wait in this loop until stepper actually says it has stopped

        time.sleep(0.2)

    logger.info("Command complete")
    time.sleep(1)#Allow some time for ongoing dispense to finish

    #renable the lights
    logger.info("Reenabling lights")
    hwCntrl.setRelayState(5, True) #Tank Light 1
    hwCntrl.setRelayState(7, True) #Tank Light 2



if __name__ == '__main__':

    logger.add('dispense_main.log', format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", rotation="100MB")

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
            logger.info("Dispense completed")
        except KeyboardInterrupt:
            logger.info("Got keyboard interrupt")
            stop_event.set()

        t.join()
        logger.info("Dispense thread closed")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Scheduler task for aquarium lights.
#
#
import logging
import grpc
import time
import json

from enum import Enum

import hardwareControl_pb2
import hardwareControl_pb2_grpc
from hardwareControl_client import HardwareControlClient

confFile = "schedule.json"

class State(Enum):
    PINIT = 0
    DISABLED = 1
    DAY = 2
    NIGHT = 3
    ECLIPSE = 4

def timeOfDayToState(hhmm, jData):
    """
        Map the time of day (given in hhmm format) to correct state per schedule
    """
    if (hhmm < jData['sunrise_hhmm']):
        return State.NIGHT

    elif (hhmm < jData['sunset_hhmm']):
        return State.DAY
    else:
        return State.NIGHT



class ScheduleSM():

    def __init__(self, jData):
        self.presentState = State.PINIT
        self.jData = jData

    def update(self, hhmm_now):
        """
            Function called to step state machine forward in time
        """
        if (self.presentState == State.PINIT):
            self.changeStateTo(timeOfDayToState(hhmm_now, self.jData))

        elif (self.presentState == State.DISABLED):
            pass

        elif (self.presentState == State.DAY):
            if (hhmm_now >= self.jData['sunset_hhmm']):
                self.changeStateTo(State.NIGHT)
            else:
                pass

        elif (self.presentState == State.NIGHT):
            if (hhmm_now > self.jData['sunrise_hhmm'] and hhmm_now < self.jData['sunset_hhmm']):
                self.changeStateTo(State.DAY)
            else:
                pass

        elif (self.presentState == State.ECLIPSE):
            pass

        else:
            print(f"ERROR: Unhandled state in update():{self.presentState}")
            #Raise exception?



    def changeStateTo(self, newState):
        """
            Function called to change state
        """

        if (newState == State.PINIT):
            pass
        elif (newState == State.DISABLED):
            pass
        elif (newState == State.DAY):
            pass
        elif (newState == State.NIGHT):
            pass
        elif (newState == State.ECLIPSE):
            pass
        else:
            print(f"ERROR: Unhandled state in changeStateTo():{newState}")
            #Raise exception?


        print(f"Scheduler: {self.presentState} --> {newState}", flush=True)
        self.presentState = newState



def main():
    with grpc.insecure_channel('localhost:50051') as channel:
        hwCntrl = HardwareControlClient(channel)
        hwCntrl.echo()

        with open(confFile,'r') as f:
            jData = json.load(f)
        print(jData['sunrise_hhmm'])
        print(jData['sunset_hhmm'])

        for tod in [600,759,801,1200,1500,1700,1801,2000,2300]:
            print(f"{tod:04d}\t{timeOfDayToState(tod, jData)}")







if __name__ == '__main__':
    main()


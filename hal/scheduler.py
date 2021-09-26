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
import datetime as dt
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


def hhmmToTime(hhmm):

    hh = int(hhmm/100)
    mm = hhmm - hh*100
    return dt.time(hour=hh, minute=mm)

def timeToHhmm(time):
    return (time.hour * 100) + time.minute


class ScheduleSM():

    def __init__(self, jData, hwCntrl):
        self.presentState = State.PINIT
        self.jData = jData
        self.hwCntrl = hwCntrl

        self.sunrise_time = hhmmToTime(jData['sunrise_hhmm'])
        self.sunset_time = hhmmToTime(jData['sunset_hhmm'])


    def update(self, dt_now):
        """
            Function called to step state machine forward in time
        """
        time_now = dt_now.time()
        self.lastTime = time_now
        if (self.presentState == State.PINIT):
            self.changeStateTo(self.timeOfDayToState(time_now, self.sunrise_time, self.sunset_time))

        elif (self.presentState == State.DISABLED):
            pass

        elif (self.presentState == State.DAY):
            if (time_now >= self.sunset_time):
                self.changeStateTo(State.NIGHT)
            elif (self.jData['eclipse_enabled'] and time_now.minute % self.jData['eclipse_frequency_min'] == 0):
                if (timeToHhmm(time_now) == timeToHhmm(self.sunrise_time)):
                    print("Skipping eclipse because DAY just started...")
                else:
                    self.eclipseEndTime = dt_now + dt.timedelta(minutes=self.jData["eclipse_duration_min"])
                    self.changeStateTo(State.ECLIPSE)

        elif (self.presentState == State.NIGHT):
            if (time_now > self.sunrise_time and time_now < self.sunset_time):
                self.changeStateTo(State.DAY)

        elif (self.presentState == State.ECLIPSE):
            if (dt_now >= self.eclipseEndTime):
                #Make sure we go to the correct state coming out of eclipse
                self.changeStateTo(self.timeOfDayToState(time_now, self.sunrise_time, self.sunset_time))

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
            # just leave the lights where they are?
            self.hwCntrl.setLightState(1, hardwareControl_pb2.LightState_Off)
            self.hwCntrl.setLightState(2, hardwareControl_pb2.LightState_Off)

        elif (newState == State.DAY):
            self.hwCntrl.setLightState(1, hardwareControl_pb2.LightState_Day)
            self.hwCntrl.setLightState(2, hardwareControl_pb2.LightState_Day)

        elif (newState == State.NIGHT):
            self.hwCntrl.setLightState(1, hardwareControl_pb2.LightState_Night)
            self.hwCntrl.setLightState(2, hardwareControl_pb2.LightState_Night)

        elif (newState == State.ECLIPSE):
            print(f"Starting eclipse! Ends at {self.eclipseEndTime}")
            self.hwCntrl.setLightState(1, hardwareControl_pb2.LightState_Night)
            self.hwCntrl.setLightState(2, hardwareControl_pb2.LightState_Night)


        else:
            print(f"ERROR: Unhandled state in changeStateTo():{newState}")
            #Raise exception?


        print(f"{self.lastTime}\tScheduler: {self.presentState} --> {newState}", flush=True)
        self.presentState = newState

    @staticmethod
    def timeOfDayToState(t, sunrise_time, sunset_time):
        """
            Map the time of day (given as time obj) to correct state per schedule
        """
        if (t < sunrise_time):
            return State.NIGHT
        elif (t < sunset_time):
            return State.DAY
        else:
            return State.NIGHT



def main():
    with grpc.insecure_channel('localhost:50051') as channel:
        hwCntrl = HardwareControlClient(channel)
        hwCntrl.echo()

        with open(confFile,'r') as f:
            jData = json.load(f)


        schSM = ScheduleSM(jData, hwCntrl)
        print("---- Running scheduler! ----")
        while (1):
            schSM.update(dt.datetime.now())
            time.sleep(30)


        print("---- Scheduler ending ----")




def test():
    hwCntrl=None
    if (1):
        with open(confFile,'r') as f:
            jData = json.load(f)
        print(jData['sunrise_hhmm'])
        print(jData['sunset_hhmm'])
        #print(timeToHhmm(dt.datetime.now()))

        schSM = ScheduleSM(jData, hwCntrl)
        print("---- Running scheduler! ----")
        t = dt.datetime.now()
        while (1):
            schSM.update(t)
            #time.sleep(0.1)
            t += dt.timedelta(seconds=30)
            #print(t)
            if (t > dt.datetime.now() + dt.timedelta(days=2)):
                break



        print("---- Scheduler ending ----")



if __name__ == '__main__':
    main()


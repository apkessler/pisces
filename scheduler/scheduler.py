#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Scheduler task for aquarium lights.
#
#
import grpc
import time
import json
import os
from enum import Enum
import datetime as dt

from loguru import logger

# Custom imports
import hardwareControl_pb2
import hardwareControl_pb2_grpc
from hwcontrol_client import HardwareControlClient


class State(Enum):
    PINIT = 0
    DISABLED = 1
    DAY = 2
    NIGHT = 3
    ECLIPSE = 4

#TODO: link to hwconfig?
lightKeys = {"TankLight1":1, "TankLight2":2, "GrowLight1":3, "GrowLight2":4}


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
        self.name=jData['name']

        self.sunrise_time = hhmmToTime(jData['sunrise_hhmm'])
        self.sunset_time = hhmmToTime(jData['sunset_hhmm'])

        for light in self.jData["lights"]:
            logger.info(f"Found light {light} ({lightKeys[light]})")


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
            for light in self.jData["lights"]:
                self.hwCntrl.setLightState(lightKeys[light], hardwareControl_pb2.LightState_Off)


        elif (newState == State.DAY):
            for light in self.jData["lights"]:
                self.hwCntrl.setLightState(lightKeys[light], hardwareControl_pb2.LightState_Day)

        elif (newState == State.NIGHT):
            for light in self.jData["lights"]:
                self.hwCntrl.setLightState(lightKeys[light], hardwareControl_pb2.LightState_Night)

        elif (newState == State.ECLIPSE):
            logger.info(f"Starting eclipse! Ends at {self.eclipseEndTime}")
            for light in self.jData["lights"]:
                self.hwCntrl.setLightState(lightKeys[light], hardwareControl_pb2.LightState_Night)


        else:
            logger.warning(f"{self.name}: Unhandled state in changeStateTo():{newState}")
            #Raise exception?


        logger.info(f"{self.name} Scheduler: {self.presentState} --> {newState}")
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


def test():
    with grpc.insecure_channel('localhost:50051') as channel:
        hwCntrl = HardwareControlClient(channel)
        with open(confFile,'r') as f:
            jData = json.load(f)

        #print(timeToHhmm(dt.datetime.now()))

        schds = [ScheduleSM(jD, hwCntrl) for jD in jData["schedules"]]

        logger.info("Running schedulers!")
        t = dt.datetime.now()
        while (1):
            for schSM in schds:
                schSM.update(t)
            time.sleep(0.1)
            t += dt.timedelta(seconds=60)
            print(t)
            if (t > dt.datetime.now() + dt.timedelta(days=2)):
                break



        logger.info("---- Scheduler ending ----")



if __name__ == '__main__':

    logger.add('scheduler.log', format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", rotation="100MB")
    logger.info("--------- SCHEDULER RESTART-------------")

    with open(os.path.join(os.path.dirname(__file__), 'scheduler.json'), 'r') as jsonfile:
        jData = json.load(jsonfile)

    try:
        with grpc.insecure_channel(jData['server']) as channel:
            hwCntrl = HardwareControlClient(channel)

            schds = [ScheduleSM(jD, hwCntrl) for jD in jData["schedules"]]
            logger.info("Schedulers initialized")

            while (1):
                for schSM in schds:
                    schSM.update(dt.datetime.now())
                time.sleep(30)

    except Exception as e:
        logger.error(f"{e}")

    logger.info(f"Stopping SCHEDULER")



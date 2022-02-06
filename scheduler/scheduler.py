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
import argparse
from enum import Enum
import datetime as dt
from loguru import logger
import threading
# Custom imports
from hwcontrol_client import HardwareControlClient
from dispense_client import dispense

class TimerState(Enum):
    PINIT = 0
    DISABLED = 1
    DAY = 2
    NIGHT = 3
    ECLIPSE = 4

#TODO: link to hwconfig?
lightKeys = {"TankLight1":1, "TankLight2":2, "GrowLight1":3, "GrowLight2":4}


def hhmmToTime(hhmm:int)->dt.time:
    '''Convert a simple time integer in form hhmm to a datetime._time object

    Parameters
    ----------
    hhmm : int
        The time to convert, as hhmm

    Returns
    -------
    dt._time
        The equivalent datetime._time object
    '''

    hh = int(hhmm/100)
    mm = hhmm - hh*100
    return dt.time(hour=hh, minute=mm)

def timeToHhmm(time:dt.time) -> int:
    ''' Convert a datetime._time object to a simple time integer in form hhmm

    Parameters
    ----------
    time : dt._time
        Time to convert

    Returns
    -------
    int
        Equivalent hhmm int
    '''
    return (time.hour * 100) + time.minute

def fake_dispense(*args):
    logger.info("Fake dispense called")
    time.sleep(5)
    logger.info("Fake dispense done")

class DispenseEvent():
    ''' An Simple state machine for running the dispense task and waiting for it to complete.
        Would be nice to eventually generalize this. '''


    def __init__(self, jData, hwCntrl:HardwareControlClient):
        self.name=jData['name']
        self.trigger_time = hhmmToTime(jData['trigger_time_hhmm'])
        self.jData = jData
        self.is_active = False
        self.hwCntrl = hwCntrl
        logger.debug(f"Made Event {self.name} of type {self.__class__} which runs at {self.trigger_time}.")
        self.last_time = None
    def update(self, dt_now:dt.datetime) -> None:

        time_now = dt_now.time()
        if (self.last_time == None):
            self.last_time = time_now

        if (self.is_active):
            if (self.thread.is_alive()):
                logger.info("Command is still running")
            else:
                logger.info("Command done!")
                self.thread.join()
                self.is_active = False

        elif (self.last_time < self.trigger_time and time_now >= self.trigger_time):
                logger.info(f"Running cmd {self.name}")
                self.is_active= True
                self.stop_event = threading.Event()
                self.thread = threading.Thread(target=dispense, args=(hwCntrl, self.jData['cmd_args']['volume_mL'], self.stop_event), daemon=True)
                self.thread.start()

        self.last_time = time_now



class ScheduleSM():

    def __init__(self, jData, hwCntrl:HardwareControlClient):
        self.presentState = TimerState.PINIT
        self.jData = jData
        self.hwCntrl = hwCntrl
        self.name=jData['name']

        self.sunrise_time = hhmmToTime(jData['sunrise_hhmm'])
        self.sunset_time = hhmmToTime(jData['sunset_hhmm'])
        self.light_mode_at_night = 'blue' if jData['blue_lights_at_night'] else 'off'

        for light in self.jData["lights"]:
            logger.info(f"Found light {light} ({lightKeys[light]})")


    def update(self, dt_now:dt.datetime) -> None:
        """
            Function called to step state machine forward in time
        """
        time_now = dt_now.time()
        self.lastTime = time_now
        if (self.presentState == TimerState.PINIT):
            self.changeStateTo(self.timeOfDayToState(time_now, self.sunrise_time, self.sunset_time))

        elif (self.presentState == TimerState.DISABLED):
            pass

        elif (self.presentState == TimerState.DAY):
            if (time_now >= self.sunset_time):
                self.changeStateTo(TimerState.NIGHT)
            elif (self.jData['eclipse_enabled'] and time_now.minute % self.jData['eclipse_frequency_min'] == 0):
                if (timeToHhmm(time_now) == timeToHhmm(self.sunrise_time)):
                    print("Skipping eclipse because DAY just started...")
                else:
                    self.eclipseEndTime = dt_now + dt.timedelta(minutes=self.jData["eclipse_duration_min"])
                    self.changeStateTo(TimerState.ECLIPSE)

        elif (self.presentState == TimerState.NIGHT):
            if (time_now > self.sunrise_time and time_now < self.sunset_time):
                self.changeStateTo(TimerState.DAY)

        elif (self.presentState == TimerState.ECLIPSE):
            if (dt_now >= self.eclipseEndTime):
                #Make sure we go to the correct state coming out of eclipse
                self.changeStateTo(self.timeOfDayToState(time_now, self.sunrise_time, self.sunset_time))

        else:
            print(f"ERROR: Unhandled state in update():{self.presentState}")
            #Raise exception?



    def changeStateTo(self, new_state: TimerState) -> None:
        '''Change the timer state to new value

        Parameters
        ----------
        newState : TimerState
            Timer state to change to
        '''

        if (new_state == TimerState.PINIT):
            pass
        elif (new_state == TimerState.DISABLED):
            # just leave the lights where they are?
            for light in self.jData["lights"]:
                self.hwCntrl.setLightColor(lightKeys[light], 'off')


        elif (new_state == TimerState.DAY):
            for light in self.jData["lights"]:
                self.hwCntrl.setLightColor(lightKeys[light], 'white')

        elif (new_state == TimerState.NIGHT):
            for light in self.jData["lights"]:
                self.hwCntrl.setLightColor(lightKeys[light], self.light_mode_at_night)

        elif (new_state == TimerState.ECLIPSE):
            logger.info(f"Starting eclipse! Ends at {self.eclipseEndTime}")
            for light in self.jData["lights"]:
                self.hwCntrl.setLightColor(lightKeys[light], 'blue')


        else:
            logger.warning(f"{self.name}: Unhandled state in changeStateTo():{new_state}")
            #Raise exception?


        logger.info(f"{self.name} Scheduler: {self.presentState} --> {new_state}")
        self.presentState = new_state

    @staticmethod
    def timeOfDayToState(t:dt.time, sunrise_time:dt.time, sunset_time:dt.time) -> TimerState:
        '''Map the time of day (given as time obj) to correct state per schedule

        Parameters
        ----------
        t : dt._time
            Time now
        sunrise_time : dt._time
            Sunrise time
        sunset_time : dt._time
            Sunset time

        Returns
        -------
        TimerState
            What state should time be in
        '''
        if (t < sunrise_time):
            return TimerState.NIGHT
        elif (t < sunset_time):
            return TimerState.DAY
        else:
            return TimerState.NIGHT



if __name__ == '__main__':



    logger.add('scheduler.log', format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", rotation="10MB", level="INFO")
    logger.info("--------- SCHEDULER RESTART-------------")

    parser = argparse.ArgumentParser(description='Run the Scheduler task')
    parser.add_argument('--simulate', action='store_true', default=False, help='Run in simulated mode')
    parser.add_argument('--days', type=int, default=2, help='How many days to run in simulated mode')

    args = parser.parse_args()

    with open(os.path.join(os.path.dirname(__file__), 'scheduler.json'), 'r') as jsonfile:
        jData = json.load(jsonfile)

    try:
        with grpc.insecure_channel(jData['server']) as channel:
            hwCntrl = HardwareControlClient(channel)

            schds = [ScheduleSM(jD, hwCntrl) for jD in jData["light_schedules"]]

            for event in jData['events']:
                if event['type'] == 'dispense':
                    schds.append(DispenseEvent(event, hwCntrl))

            logger.info("Schedulers initialized")


            #Simulation mode!
            if (args.simulate):
                t = dt.datetime.now()
                while (1):
                    for schSM in schds:
                        schSM.update(t)
                    time.sleep(0.1)
                    t += dt.timedelta(seconds=60)
                    print(t, flush=True)
                    if (t > dt.datetime.now() + dt.timedelta(days=args.days)):
                        logger.info("Simulation complete!")
                        break
            else: #Real mode
                while (1):
                    for schSM in schds:
                        schSM.update(dt.datetime.now())
                    time.sleep(30)

    except Exception as e:
        logger.error(f"{e}")

    logger.info(f"Stopping SCHEDULER")



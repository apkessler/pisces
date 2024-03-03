#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Scheduler task for aquarium lights.
#
#
from typing import Callable
import grpc
import time
import os
from enum import Enum
import datetime as dt
from loguru import logger

# Custom imports
from hwcontrol_client import HardwareControlClient
from dispense_client import dispense


class TimerState(Enum):
    PINIT = 0
    DISABLED = 1
    DAY = 2
    NIGHT = 3
    ECLIPSE = 4


# TODO: link to hwconfig, since these are really the order of things defined in hwconfig
lightKeys = {
    "TankLight1": 1,
    "TankLight2": 2,
    "outlet1": 3,
    "outlet2": 4,
    "outlet3": 5,
    "outlet4": 6,
}


def hhmmToTime(hhmm: int) -> dt.time:
    """Convert a simple time integer in form hhmm to a datetime._time object

    Parameters
    ----------
    hhmm : int
        The time to convert, as hhmm

    Returns
    -------
    dt._time
        The equivalent datetime._time object
    """

    hh = int(hhmm / 100)
    mm = hhmm - hh * 100
    return dt.time(hour=hh, minute=mm)


def timeToHhmm(time: dt.time) -> int:
    """Convert a datetime._time object to a simple time integer in form hhmm

    Parameters
    ----------
    time : dt._time
        Time to convert

    Returns
    -------
    int
        Equivalent hhmm int
    """
    return (time.hour * 100) + time.minute


def fake_dispense(*args):
    logger.info("Fake dispense called")
    time.sleep(5)
    logger.info("Fake dispense done")


class GenericEvent:
    """An Simple state machine for running the dispense task and waiting for it to complete.
    Would be nice to eventually generalize this."""

    def __init__(self, name, time_hhmm, callback, hwCntrl: HardwareControlClient):
        self.name = name
        self.trigger_time = hhmmToTime(time_hhmm)
        # self.jData = jData
        self.is_active = False
        self.hwCntrl = hwCntrl
        logger.debug(
            f"Made Event {self.name} of type {self.__class__} which runs at {self.trigger_time}."
        )
        self.last_time = None
        self.callback = callback
        # self.stop_callback = None

    def update(self, dt_now: dt.datetime) -> None:
        time_now = dt_now.time()
        if self.last_time == None:
            self.last_time = time_now

        if self.last_time < self.trigger_time and time_now >= self.trigger_time:
            logger.info(f"Running cmd {self.name}")
            if self.callback != None:
                self.callback()

        self.last_time = time_now


class LightTimer:
    def __init__(self, name: str, jData: dict, hwCntrl: HardwareControlClient):
        self.presentState = TimerState.PINIT
        self.jData = jData
        self.hwCntrl = hwCntrl
        self.name = name

        self.sunrise_time = hhmmToTime(jData["sunrise_hhmm"])
        self.sunset_time = hhmmToTime(jData["sunset_hhmm"])
        self.light_mode_at_night = "blue" if jData["blue_lights_at_night"] else "off"

        for light in self.jData["lights"]:
            logger.info(f"Found light {light} ({lightKeys[light]})")

    def update(self, dt_now: dt.datetime) -> None:
        """
        Function called to step state machine forward in time
        """
        time_now = dt_now.time()
        self.lastTime = time_now
        if self.presentState == TimerState.PINIT:
            self.changeStateTo(
                self.timeOfDayToState(time_now, self.sunrise_time, self.sunset_time)
            )

        elif self.presentState == TimerState.DISABLED:
            pass

        elif self.presentState == TimerState.DAY:
            if time_now >= self.sunset_time:
                self.changeStateTo(TimerState.NIGHT)
            elif (
                self.jData["eclipse_enabled"]
                and time_now.minute % self.jData["eclipse_frequency_min"] == 0
            ):
                if timeToHhmm(time_now) == timeToHhmm(self.sunrise_time):
                    print("Skipping eclipse because DAY just started...")
                else:
                    self.eclipseEndTime = dt_now + dt.timedelta(
                        minutes=self.jData["eclipse_duration_min"]
                    )
                    self.changeStateTo(TimerState.ECLIPSE)

        elif self.presentState == TimerState.NIGHT:
            if time_now > self.sunrise_time and time_now < self.sunset_time:
                self.changeStateTo(TimerState.DAY)

        elif self.presentState == TimerState.ECLIPSE:
            if dt_now >= self.eclipseEndTime:
                # Make sure we go to the correct state coming out of eclipse
                self.changeStateTo(
                    self.timeOfDayToState(time_now, self.sunrise_time, self.sunset_time)
                )

        else:
            print(f"ERROR: Unhandled state in update():{self.presentState}")
            # Raise exception?

    def changeStateTo(self, new_state: TimerState) -> None:
        """Change the timer state to new value

        Parameters
        ----------
        newState : TimerState
            Timer state to change to
        """

        if new_state == TimerState.PINIT:
            pass
        elif new_state == TimerState.DISABLED:
            pass
            # just leave the lights where they are?

        elif new_state == TimerState.DAY:
            for light in self.jData["lights"]:
                self.hwCntrl.setLightColor(lightKeys[light], "white")

        elif new_state == TimerState.NIGHT:
            for light in self.jData["lights"]:
                self.hwCntrl.setLightColor(lightKeys[light], self.light_mode_at_night)

        elif new_state == TimerState.ECLIPSE:
            logger.info(f"Starting eclipse! Ends at {self.eclipseEndTime}")
            for light in self.jData["lights"]:
                self.hwCntrl.setLightColor(lightKeys[light], "blue")

        else:
            logger.error(f"{self.name}: Unhandled state in changeStateTo():{new_state}")
            # Raise exception?

        logger.debug(f"{self.name} Scheduler: {self.presentState} --> {new_state}")
        self.presentState = new_state

    @staticmethod
    def timeOfDayToState(
        t: dt.time, sunrise_time: dt.time, sunset_time: dt.time
    ) -> TimerState:
        """Map the time of day (given as time obj) to correct state per schedule

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
        """
        if t < sunrise_time:
            return TimerState.NIGHT
        elif t < sunset_time:
            return TimerState.DAY
        else:
            return TimerState.NIGHT

    def resume_schedule(self, dt_now: dt.datetime) -> None:
        """[summary]

        Parameters
        ----------
        dt_now : dt.datetime
            [description]
        """
        logger.info(f"Resuming schedule on {self.name}")
        self.changeStateTo(
            self.timeOfDayToState(dt_now.time(), self.sunrise_time, self.sunset_time)
        )

    def disable_schedule(self) -> None:
        """[summary]"""
        logger.info(f"Disabling schedule on {self.name}")
        self.changeStateTo(TimerState.DISABLED)


class OutletTimer(LightTimer):
    def __init__(self, name: str, jData: dict, hwCntrl: HardwareControlClient):
        """OutletTimers are just barebones LightTimers

        Parameters
        ----------
        name : str
            Name of outlet timer
        jData : dict
            Configuration JSON dict
        hwCntrl : HardwareControlClient
            hwCntrl stub
        """
        jData["blue_lights_at_night"] = False
        jData["lights"] = [name]
        jData["eclipse_enabled"] = False
        super().__init__(name, jData, hwCntrl)

        # Disable the timer if this isn't in timer mode...
        if jData["mode"] in ["off", "on"]:
            self.changeStateTo(TimerState.DISABLED)
            self.hwCntrl.setLightColor(
                lightKeys[name], "white" if jData["mode"] == "on" else "off"
            )  # Manually set the outlet state


class Scheduler(object):
    def __init__(self, hwCntrl):
        self.hwCntrl = hwCntrl
        self.schds = []

    def build_light_timers(self, jData: dict) -> None:
        """Build all Light Timers in config dict

        Parameters
        ----------
        jData : dict
            Dict of JSON Data
        """
        self.schds += [LightTimer(key, jD, self.hwCntrl) for key, jD in jData.items()]

    def build_outlet_timers(self, jData: dict) -> None:
        """Build all OutletTimer objects from config dict

        Parameters
        ----------
        jData : dict
            Dict of JSON data
        """
        self.schds += [OutletTimer(key, jD, self.hwCntrl) for key, jD in jData.items()]

    def add_event(self, name: str, time_hhmm: int, callback: Callable) -> None:
        """Create and append discrete event

        Parameters
        ----------
        name : str
            Name of event
        time_hhmm : int
            Time for event to occur
        callback : function
            Callback function associated with event
        """
        self.schds.append(GenericEvent(name, time_hhmm, callback, self.hwCntrl))

    def update(self, now: dt.datetime):
        """Called to update every timer object owned by this Scheduler

        Parameters
        ----------
        now : dt.datetime
            The current time
        """
        for schSM in self.schds:
            schSM.update(now)

    def disable_timers(self, timer_list: list):
        """Disable matching timers by name

        Parameters
        ----------
        timer_list : list
            List of names of timers to disable
        """
        for name in timer_list:
            found = False
            for schSM in self.schds:
                if schSM.name == name:
                    schSM.disable_schedule()
                    found = True
            if not found:
                logger.error(f"No Timer named {name} found!")

    def resume_timers(self, timer_list: list):
        """Resume matching timers by name

        Parameters
        ----------
        timer_list : list
            List of names of timers to enable
        """
        now = dt.datetime.now()
        for schSM in self.schds:
            if schSM.name in timer_list:
                schSM.resume_schedule(now)


if __name__ == "__main__":
    logger.add(
        os.path.join(os.path.dirname(__file__), "../data/scheduler.log"),
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10MB",
    )
    logger.info("--------- SCHEDULER RESTART-------------")

    try:
        with grpc.insecure_channel("localhost:50051") as channel:
            hwCntrl = HardwareControlClient(channel)

            schdlr = Scheduler(hwCntrl)

            while 1:
                schdlr.update(dt.datetime.now())
                time.sleep(30)

    except Exception as e:
        logger.error(f"{e}")

    logger.info(f"Stopping SCHEDULER")

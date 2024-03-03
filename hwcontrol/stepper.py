#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Stepper Motor Class
#
#

import time
import threading
import queue
from enum import Enum
from loguru import logger

# Note: Lazy import of gpiozero module in __init__


class StepMode(Enum):
    FULL_STEP = 0
    HALF_STEP = 1
    QUARTER_STEP = 2
    EIGTH_STEP = 3
    SIXTEENTH_STEP = 4


class StepperMotor(object):
    def __init__(self, step, dir, nen, ms1, ms2, ms3, use_mock_hw=False):
        # Lazy import here to better support mock hw case
        if use_mock_hw:
            import fakegpio as gz

            logger.info("Loaded fakegpio module for stepper.")
        else:
            try:
                import gpiozero as gz

                logger.info("Loaded gpiozero module for stepper")
            except ModuleNotFoundError:
                msg = "Unable to load gpiozero module for stepper! Not running on RPi?"
                logger.error(msg)
                raise Exception(msg)

        self.gpio_step = gz.DigitalOutputDevice(pin=step)
        self.gpio_dir = gz.DigitalOutputDevice(pin=dir)
        self.gpio_nen = gz.DigitalOutputDevice(pin=nen)

        self.gpios_msx = [None, None, None]

        if ms1:
            self.gpios_msx[0] = gz.DigitalOutputDevice(pin=ms1)

        if ms2:
            self.gpios_msx[1] = gz.DigitalOutputDevice(pin=ms2)

        if ms3:
            self.gpios_msx[2] = gz.DigitalOutputDevice(pin=ms3)

        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_active_flag = threading.Event()

        self.stop_event.clear()
        self.is_active_flag.clear()

        self.gpio_nen.on()  # Assert to disable driver

        self.thread = threading.Thread(target=self._run, args=(), daemon=True)
        self.thread.start()

    def enableDriver(self):
        logger.debug("Enabling stepper")
        self.gpio_nen.off()

    def disableDriver(self):
        logger.debug("Disabling stepper")
        self.gpio_nen.on()

    def takeStep(self, delay_s=0.005):
        """
        Take one step. Driver must already be enabled
        """
        self.gpio_step.on()
        time.sleep(delay_s)
        self.gpio_step.off()
        time.sleep(delay_s)

    def sendCommand(self, steps, isReverse=False, mode=StepMode.FULL_STEP):
        cmd = {"steps": steps, "isReverse": isReverse, "mode": mode}
        logger.debug(f"Enqueing cmd {cmd}")
        self.queue.put(cmd, timeout=1)

    def sendStop(self):
        """Tell the stepper thread to stop what its doing"""
        self.stop_event.set()

    def getIsActive(self):
        """Return whether or not stepper is currently doing something"""
        return self.is_active_flag.is_set()

    def setMode(self, mode):
        """
        Set the MS1,MS2, and MS3 bits appropriately. (Looks at bits 0,1,2 of mode value)
        """

        mask = 0x1
        for pin in self.gpios_msx:
            if mask & mode.value:
                pin.on()
            else:
                pin.off()

            mask = mask << 1

        print(f"{mode} ({mode.value}):{[g.is_active for g in self.gpios_msx]}")

    def _run(self):
        """
        This method should run as in its own thread. It waits for commands to come in
        over the message queue, then executes them.
        """

        logger.info("Running pump cmd handler thread")

        while 1:
            cmd = self.queue.get()  # Blocking wait for new command

            logger.debug(f"Dequeing cmd: {cmd}")
            self.is_active_flag.set()

            if cmd["isReverse"]:
                self.gpio_dir.on()
            else:
                self.gpio_dir.off()

            self.stop_event.clear()  # Clear any lingering stop events
            self.enableDriver()
            time.sleep(0.1)

            for i in range(cmd["steps"]):
                self.takeStep()
                if self.stop_event.is_set():
                    logger.info("Stepper thread got STOP command")
                    break

            time.sleep(0.1)

            self.disableDriver()

            self.is_active_flag.clear()
            logger.info("Done with stepper cmd")

        logger.error("Stepper run thread exiting (uh-oh)")

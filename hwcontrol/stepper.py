#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Stepper Motor Class
#
#

import time
import threading, queue
from enum import Enum
import logging

#Note: Lazy import of gpiozero module in __init__

class StepMode(Enum):
    FULL_STEP = 0
    HALF_STEP = 1
    QUARTER_STEP = 2
    EIGTH_STEP = 3
    SIXTEENTH_STEP = 4

class StepperMotor(object):

    def __init__(self, step, dir, nen, ms1, ms2, ms3, use_mock_hw=False):

        #Lazy import here to better support mock hw case
        if (use_mock_hw):
            import fakegpio as gz
            logging.info("Loaded fakegpio module for stepper.")
        else:
            try:
                import gpiozero as gz
                logging.info("Loaded gpiozero module for stepper")
            except ModuleNotFoundError:
                msg = "Unable to load gpiozero module for stepper! Not running on RPi?"
                logging.error(msg)
                raise Exception(msg)

        self.gpio_step = gz.DigitalOutputDevice(pin=step)
        self.gpio_dir =  gz.DigitalOutputDevice(pin=dir)
        self.gpio_nen =   gz.DigitalOutputDevice(pin=nen)


        self.gpios_msx = [None, None, None]

        if ms1:
            self.gpios_msx[0] = gz.DigitalOutputDevice(pin=ms1)

        if ms2:
            self.gpios_msx[1] = gz.DigitalOutputDevice(pin=ms2)

        if ms3:
            self.gpios_msx[2] = gz.DigitalOutputDevice(pin=ms3)

        self.queue = queue.Queue()

        self.gpio_nen.on() #Assert to disable driver

        self.thread = threading.Thread(target=self._run, args=(), daemon=True)
        self.thread.start()


    def enableDriver(self):
        logging.debug("Enabling stepper")
        self.gpio_nen.off()

    def disableDriver(self):
        logging.debug("Disabling stepper")
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
        cmd = {'steps':steps, 'isReverse':isReverse, 'mode':mode}
        logging.debug(f"Enqueing cmd {cmd}")
        self.queue.put(cmd, timeout=1)


    def setMode(self, mode):
        """
            Set the MS1,MS2, and MS3 bits appropriately. (Looks at bits 0,1,2 of mode value)
        """

        mask = 0x1
        for pin in self.gpios_msx:
            if (mask & mode.value):
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

        logging.info(f"Running pump cmd handler thread")

        while (1):
            cmd = self.queue.get() #Blocking wait for new command

            logging.debug(f"Dequeing cmd: {cmd}")

            if (cmd['isReverse']):
                self.gpio_dir.on()
            else:
                self.gpio_dir.off()

            self.enableDriver()
            time.sleep(0.1)

            for i in range(cmd['steps']):
                logging.debug(f"Rising edge {i}")
                self.takeStep()

            time.sleep(0.1)

            self.disableDriver()

            logging.info(f"Done with stepper cmd")

        logging.debug(f"Stepper run thread compelte")


def main():


    stepperObj = StepperMotor('GPIO17', 'GPIO27', 'GPIO22', None, None, None)

    while (1):
        cmd = input("Input command: (dir,mode,steps): ")
        tokens = [int(x) for x in cmd.split(',')]
        dir =tokens[0]
        mode = StepMode(tokens[1])
        steps = tokens[2]
        #print(f"DIR:{dir}, Mode:{mode}, Steps:{steps}")

        stepperObj.sendCommand(steps, dir, mode)
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except KeyboardInterrupt:
        print("Ending program")

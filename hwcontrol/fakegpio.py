#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Fake GPIO class for use when not on raspberry pi
#
#

LOG_FILE = 'gpiostate.txt' #This is where state of GPIO regsiters are written to

class DigitalOutputDevice():

    instances = []
    def __init__(self, pin="", active_high=""):
        self.pin = pin
        self.active_high = active_high
        self.state = 0
        DigitalOutputDevice.instances.append(self)

    def on(self):
        self.state = 1
        DigitalOutputDevice.printGpios()

    def off(self):
        self.state = 0
        DigitalOutputDevice.printGpios()

    @property
    def is_active(self):
        return self.state


    @classmethod
    def printGpios(cls):
        with open(LOG_FILE, mode='a') as f:
            f.write(' '.join([str(x.is_active) for x in cls.instances]) + '\n')
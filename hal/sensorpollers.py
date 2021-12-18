#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Sensor Poller Class
# Andrew Kessler 2021
#

import glob
import time
import threading
from collections import deque
import logging
import datetime as dt
import math
try:
    import AtlasI2C as Atlas
except ModuleNotFoundError:
    print("Unable to fully import AtlasI2C library")
    #ok for simulated system

import random

class ThermometerPoller(object):
    """
        The temperature poller thread gets a new reading from the temperature sensor at a fixed rate, and
        pushes it onto the RIGHT side of a deque of length 1. Main thread can pop (or peek) from
        the left side to get the most recent sensor reading with timestamp. If pop(), needs to
        handle case of no data on dequeue.

        TODO: Directly adapted from sample code. Should clean up, comment, and add error handling
        TODO: move all hardcoded stuff to config file -- possibly to HardwareMap object?
    """
    def __init__(self, interval_s = 5):
        self.interval_s = interval_s
        self.deque = deque(maxlen=1)
        try:
            base_dir = '/sys/bus/w1/devices/'
            device_folder = glob.glob(base_dir + '28*')[0]
            self.device_file = device_folder + '/w1_slave'
            logging.info(f"Found temperature sensor: {device_folder}")

            self.thread = threading.Thread(target=self._poll, args=(), daemon=True)
            self.thread.start()
        except IndexError:
            logging.warn("Temperature sensor not found!!!")
            v = (dt.datetime.now(),  -273) #Push a fake reading so code will run
            self.deque.append(v)


    def getLatestDatum(self):
        return self.deque[0] #Peek from Deck to never consume

    def _poll(self):
        """
            This method should run as in its own thread.
        """

        logging.info(f"Starting thermometer polling thread")

        def read_temp_raw():
            f = open(self.device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines

        def read_temp():
            lines = read_temp_raw()
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = read_temp_raw()
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
                #temp_f = temp_c * 9.0 / 5.0 + 32.0
                return temp_c

        while True:

            temp_c = read_temp()
            v = (dt.datetime.now(),  temp_c)
            logging.debug(f"THERM: Pushing ({v[0].strftime('%Y-%m-%d-%H:%M:%S')}, {v[1]:.3f}°C) onto deque")
            self.deque.append(v)
            time.sleep(self.interval_s)

class PhSensorPoller(object):
    """
        The pH poller thread gets a new reading from the pH sensor every couple of seconds, and
        pushes it onto the RIGHT side of a deque of length 1. Main thread can pop (or peek) from
        the left side to get the most recent sensor reading with timestamp. If pop(), needs to
        handle case of no data on dequeue.

        TODO: Directly adapted from sample code. Should clean up, comment, and add error handling
        TODO: move all hardcoded stuff to config file -- possibly to HardwareMap object?
    """
    def __init__(self, interval_s = 5):
        self.interval_s = interval_s
        self.readDelay_s = 3
        self.deque = deque(maxlen=1)
        try:
            self.phSensor = Atlas.AtlasI2C(address = 99, moduletype = "pH")

            logging.info(f"Found ph sensor!")

            self.thread = threading.Thread(target=self._poll, args=(), daemon=True)
            self.thread.start()
        except IndexError:
            logging.warn("Ph sensor not found!!!")
            v = (dt.datetime.now(),  0) #Push a fake reading so code will run
            self.deque.append(v)


    def getLatestDatum(self):
        return self.deque[0] #Peek from Deck to never consume

    def _poll(self):
        """
            This method should run as in its own thread.
        """

        logging.info(f"Starting PH polling thread")

        while (True):
            self.phSensor.write('R')
            time.sleep(self.readDelay_s)
            try:
                theData = float(self.phSensor.read())  #TODO add error handling for failed reads
            except ValueError as e:
                logging.warning(f"Problem with ph reading! {e}")
                theData = 0.0

            v = (dt.datetime.now(), theData)
            logging.debug(f"PH: Pushing ({v[0].strftime('%Y-%m-%d-%H:%M:%S')}, {v[1]:.3f}) onto deque")
            self.deque.append(v)

            time.sleep(max(self.interval_s - self.readDelay_s, 0.1))

class SimulatedPoller(object):
    """
        A simulated poller for fake sensors
    """
    def __init__(self, interval_s = 5, minV=0, maxV=100, stepV=0.1):
        self.interval_s = interval_s
        self.minV = minV
        self.maxV = maxV
        self.stepV = stepV

        self.deque = deque(maxlen=1)
        self.thread = threading.Thread(target=self._poll, args=(), daemon=True)
        self.thread.start()



    def getLatestDatum(self):
        return self.deque[0] #Peek from Deck to never consume

    def _poll(self):
        """
            This method should run as in its own thread.
        """

        logging.info(f"Starting fake polling thread")

        while True:

            value = random.random()*(self.maxV - self.minV) + self.minV
            v = (dt.datetime.now(),  value)
            logging.debug(f"THERM: Pushing ({v[0].strftime('%Y-%m-%d-%H:%M:%S')}, {v[1]:.3f}°C) onto deque")
            self.deque.append(v)
            time.sleep(self.interval_s)

def main():

    T = ThermometerPoller()
    P = PhSensorPoller()

    while (1):
        time.sleep(5) #give things a chance to start
        logging.info(f"Temp: {T.getLatestDatum()}")
        logging.info(f"pH: {P.getLatestDatum()}")
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    try:
        main()
    except KeyboardInterrupt:
        print("Ending program")

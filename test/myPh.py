#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Custom test script for Atlas Scientific ezo pH

import AtlasI2C as Atlas
import time
import threading
from collections import deque
import logging
import datetime as dt

# logger = logging.getLogger(__name__)


def thread_poll(theDeque, phDev, period_s):
    while True:
        phDev.write("R")
        time.sleep(period_s)
        v = (dt.datetime.now().time(), phDev.read())
        theDeque.append(v)
        time.sleep(1)


def main():
    tmpDevice = Atlas.AtlasI2C()

    tmpDevice.set_i2c_address(99)
    response = tmpDevice.query("I")
    moduletype = response.split(",")[1]

    name = tmpDevice.query("name,?").split(",")[1]

    phSensor = Atlas.AtlasI2C(address=99, moduletype=moduletype, name=name)

    print(f"Setup: {phSensor.get_device_info()}", flush=True)

    theDeque = deque(maxlen=1)
    t = threading.Thread(target=thread_poll, args=(theDeque, phSensor, 3), daemon=True)
    t.start()
    while True:
        try:
            while True:
                s = theDeque.popleft()
                print(f"Got {s} --> {s[1]}", flush=True, end="")
        except IndexError:
            pass
            print("{}", flush=True)

        time.sleep(1)


if __name__ == "__main__":
    # # create logger
    # logger.setLevel(logging.DEBUG)

    # # create console handler and set level to debug
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)

    # # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # # add formatter to ch
    # ch.setFormatter(formatter)

    # # add ch to logger
    # logger.addHandler(ch)

    # logger.info("Test!")
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Custom test script for Atlas Scientific ezo pH

import AtlasI2C as Atlas
import time


tmpDevice = Atlas.AtlasI2C()

tmpDevice.set_i2c_address(99)
response = tmpDevice.query("I")
moduletype = response.split(",")[1]

name = tmpDevice.query("name,?").split(",")[1]


print(f"ModuleType={moduletype}")
print(f"name={name}")

phSensor = Atlas.AtlasI2C(address = 99, moduletype = moduletype, name = name)

print(phSensor.get_device_info())

print(f"Timeout={phSensor.long_timeout}")

for i in range(10):
    phSensor.write("R")
    time.sleep(3)
    print(f"pH={phSensor.read()}",flush=True)
    time.sleep(1)
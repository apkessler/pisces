#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Gpio test script
#
#

import gpiozero as gz
import time


# Pinout - TODO, move to config?
relay_gpio_map = [
    "GPIO5",
    "GPIO6",
    "GPIO13",
    "GPIO16",
    "GPIO19",
    "GPIO20",
    "GPIO21",
    "GPIO26",
]  # GPIOxx pins per Raspi Conventoin

relay_gpio_objs = [
    gz.DigitalOutputDevice(pin=p, active_high=False) for p in relay_gpio_map
]


def main():
    for r in relay_gpio_objs:
        print(r, flush=True)

    c = input("\nPress any key to continue...")

    for inx, relay in enumerate(relay_gpio_objs):
        print(f"Turning on Relay[{inx}]", flush=True)
        relay.on()
        print(f"\t{relay.is_active}", flush=True)
        c = input("\n Press any key to continue...")

        print(f"Turning off Relay[{inx}]", flush=True)
        relay.off()
        print(f"\t{relay.is_active}", flush=True)
        c = input("\nPress any key to continue...")

    while 1:
        pass


if __name__ == "__main__":
    main()

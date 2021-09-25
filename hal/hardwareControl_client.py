#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Client for Raspisces Hardware Abstraction Layer Servicer (HAL)
#
#

import logging
import grpc
import time

import hardwareControl_pb2
import hardwareControl_pb2_grpc

class HardwareControlClient():

    def __init__(self, channel):
        self.stub = hardwareControl_pb2_grpc.HardwareControlStub(channel)


    def getTemperature_degC(self):
        """
            Get the latest temperature reading.
        """
        response = self.stub.GetTemperature(hardwareControl_pb2.Empty())
        return response.temperature_degC

    def echo(self, payload='Test123'):
        """
            Send and receive a loopback test of given string.
        """
        response = self.stub.Echo(hardwareControl_pb2.EchoRequest(payload=payload))
        print(f"Echo returned: {response.payback}")

    def setRelayState(self, chn, isEngaged):
        """
            Set state on given channel to given state
        """
        response = self.stub.SetRelayState(hardwareControl_pb2.RelayState(channel=chn, isEngaged=isEngaged))

    def getRelayStates(self):
        """
            Get all relay states as list.
            Unpack from GRPC object and return as native Python list.
        """
        response = self.stub.GetRelayStates(hardwareControl_pb2.Empty())
        return [r.isEngaged for r in response.states]

    def getLightStates(self):
        """
            Get all light states as list.
            Unpack from GRPC object and return as native Python list.
        """
        response = self.stub.GetLightStates(hardwareControl_pb2.Empty())
        return [r.state for r in response.states]

def test():
    """
        Exercise available interfaces for testing.
    """
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        hwCntrl = HardwareControlClient(channel)
        hwCntrl.echo()

        print(f"Light states: {hwCntrl.getLightStates()}")

        print(f"Temperature={hwCntrl.getTemperature_degC():.2f} dC")
        print(f"Relay states: {hwCntrl.getRelayStates()}")

        hwCntrl.setRelayState(1, True)
        print(f"Relay states: {hwCntrl.getRelayStates()}")
        time.sleep(2)
        hwCntrl.setRelayState(1, False)

        print(f"Relay states: {hwCntrl.getRelayStates()}")

if __name__ == '__main__':
    logging.basicConfig()
    test()







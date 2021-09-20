#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Client for Raspisces Hardware Abstraction Layer Servicer (HAL)
#
#

import logging
import grpc

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

        print(f"Temperature={hwCntrl.getTemperature_degC():.2f} dC")

        hwCntrl.setRelayState(2, True)
        hwCntrl.setRelayState(3, False)

if __name__ == '__main__':
    logging.basicConfig()
    test()







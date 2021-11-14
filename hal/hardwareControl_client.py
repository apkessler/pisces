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

    def getPH(self):
        """
            Get the latest pH reading.
        """
        response = self.stub.GetPH(hardwareControl_pb2.Empty())
        return response.pH

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

    def setLightState(self, lightId, state):
        """
            Set state on given light to given state
        """
        response = self.stub.SetLightState(hardwareControl_pb2.LightState(lightId=lightId, state=state))

    def getLightStates(self):
        """
            Get all light states as list.
            Unpack from GRPC object and return as native Python list.
        """
        response = self.stub.GetLightStates(hardwareControl_pb2.Empty())
        return [r.state for r in response.states]

    def moveStepper(self, numSteps, isReverse=False):
        """
            Move stepper motor specified number of steps
        """
        response = self.stub.MoveStepper(hardwareControl_pb2.StepperCommand(numSteps=numSteps, isReverse=isReverse))

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


        for i in range(1,9):
            hwCntrl.setRelayState(i, True)
            #print(f"Relay states: {hwCntrl.getRelayStates()}")
            time.sleep(2)
            hwCntrl.setRelayState(i, False)
            time.sleep(2)

        return


        print(f"Light states: {hwCntrl.getLightStates()}")



        print(f"Temperature={hwCntrl.getTemperature_degC():.2f} dC")
        print(f"pH={hwCntrl.getPH():.2f}")

        hwCntrl.moveStepper(500)
        time.sleep(2)
        hwCntrl.moveStepper(500, isReverse=True)

        # print(f"Relay states: {hwCntrl.getRelayStates()}")

        # hwCntrl.setRelayState(1, True)
        # print(f"Relay states: {hwCntrl.getRelayStates()}")
        # time.sleep(2)
        # hwCntrl.setRelayState(1, False)

        # print(f"Relay states: {hwCntrl.getRelayStates()}")

        # hwCntrl.setLightState(1, hardwareControl_pb2.LightState_Day)
        # print(f"Light states: {hwCntrl.getLightStates()}")
        # time.sleep(2)
        # hwCntrl.setLightState(1, hardwareControl_pb2.LightState_Off)
        # print(f"Light states: {hwCntrl.getLightStates()}")


if __name__ == '__main__':
    logging.basicConfig()
    test()







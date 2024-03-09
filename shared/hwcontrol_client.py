#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Client for Raspisces Hardware Abstraction Layer Servicer (HAL)
#
#

from typing import List
import hardwareControl_pb2
import hardwareControl_pb2_grpc

ColorMap = {
    "off": hardwareControl_pb2.LightColor_Off,
    "white": hardwareControl_pb2.LightColor_White,
    "blue": hardwareControl_pb2.LightColor_Blue,
}


def color_enum_to_name(e: hardwareControl_pb2.LightColorEnum) -> str:
    for color_name, color_enum in ColorMap.items():
        if e == color_enum:
            return color_name

    return "???"


def color_name_to_enum(color: str) -> hardwareControl_pb2.LightColorEnum:
    return ColorMap[color]  # This will throw KeyError if color str is invalid


class HardwareControlClient:
    def __init__(self, channel):
        self.stub = hardwareControl_pb2_grpc.HardwareControlStub(channel)

    def getTemperature_degC(self) -> float:
        """
        Get the latest temperature reading in degrees C
        """
        response = self.stub.GetTemperature(hardwareControl_pb2.Empty())
        return response.temperature_degC

    def getTemperature_degF(self) -> float:
        """
        Get the latest temperature reading in degrees F
        """
        response = self.stub.GetTemperature(hardwareControl_pb2.Empty())
        return (response.temperature_degC * 9.0) / 5.0 + 32.0

    def getPH(self) -> float:
        """
        Get the latest pH reading.
        """
        response = self.stub.GetPH(hardwareControl_pb2.Empty())
        return response.pH

    def echo(self, payload="Test123") -> None:
        """
        Send and receive a loopback test of given string.
        """
        response = self.stub.Echo(hardwareControl_pb2.EchoRequest(payload=payload))
        print(f"Echo returned: {response.payback}")

    def setRelayState(self, chn, isEngaged) -> None:
        """
        Set state on given channel to given state
        """
        _ = self.stub.SetRelayState(
            hardwareControl_pb2.RelayState(channel=chn, isEngaged=isEngaged)
        )

    def getRelayStates(self) -> List[bool]:
        """
        Get all relay states as list.
        Unpack from GRPC object and return as native Python list.
        """
        response = self.stub.GetRelayStates(hardwareControl_pb2.Empty())
        return [r.isEngaged for r in response.states]

    def setLightColor(self, lightId: int, color_name: str, scope: str = "") -> None:
        """Set given light to given color.

        Parameters
        ----------
        lightId : int
            Light to change
        color_name : str
            One of ['off', 'white', 'blue']
        scope : str, optional
            Command scope, by default ""
        """

        _ = self.stub.SetLightColor(
            hardwareControl_pb2.LightColor(
                lightId=lightId, color_enum=color_name_to_enum(color_name), scope=scope
            )
        )

    def getLightColors(self) -> List[str]:
        """Get all light colors and return as list of strings.
            Unpack from GRPC object and return as native Python list.

        Returns
        -------
        List[str]
            List of current light colors
        """
        response = self.stub.GetLightColors(hardwareControl_pb2.Empty())
        return [color_enum_to_name(r.color_enum) for r in response.colors]

    def moveStepper(self, numSteps: int, isReverse: bool = False) -> None:
        """
        Move stepper motor specified number of steps
        """
        _ = self.stub.MoveStepper(
            hardwareControl_pb2.StepperCommand(numSteps=numSteps, isReverse=isReverse)
        )

    def stopStepper(self) -> None:
        """Stop the stepper motor from doing any motion"""
        _ = self.stub.StopStepper(hardwareControl_pb2.Empty())

    def getIsStepperActive(self) -> bool:
        """Get true/false if stepper is active right now"""
        response = self.stub.IsStepperActive(hardwareControl_pb2.Empty())
        return response.isActive

    def setScope(self, scope="") -> None:
        """Set the Light Control scope."""
        _ = self.stub.SetScope(hardwareControl_pb2.Scope(scope=scope))

    def setPhSensorSampleTime(self, time_msec: int) -> None:
        """time of 0 = return to default"""
        _ = self.stub.SetPHSampleTime(
            hardwareControl_pb2.SampleTime(sample_time_msec=time_msec)
        )

    def getPhSensorSampleTime_ms(self) -> int:
        response = self.stub.GetPHSampleTime(hardwareControl_pb2.Empty())
        return response.sample_time_msec

    def sendPhSensorCommand(self, cmd: str) -> str:
        response = self.stub.SendPHCommand(hardwareControl_pb2.PHCommand(cmd=cmd))
        return response.response

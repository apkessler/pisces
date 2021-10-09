#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Server for RasPisces Hardware Abstraction Layer Servicer (HAL)
#
#

from concurrent import futures
import logging
import grpc, json
from collections import namedtuple
import os

import hardwareControl_pb2
import hardwareControl_pb2_grpc

import gpiozero as gz

#Custom libraries
import stepper
import sensorpollers

class Light():
    """
        Object to represent a 3way aquarium light
    """
    def __init__(self, name, enable_relay, mode_relay):
        self.name = name
        self.enable_relay = enable_relay
        self.mode_relay = mode_relay

        self.state = hardwareControl_pb2.LightState_Off

    def getState(self):
        return self.state

    def getStateStr(self):
        if (self.state == hardwareControl_pb2.LightState_Off):
            return "Off"
        if (self.state == hardwareControl_pb2.LightState_Day):
            return "Day"
        if (self.state == hardwareControl_pb2.LightState_Night):
            return "Night"

        return "???"

    def changeState(self, state):
        if (state == hardwareControl_pb2.LightState_Off):
            print(f"Turning {self.name} off!")
            self.enable_relay.gpioObj.off()
            self.mode_relay.gpioObj.off() #Not strictly necessary, but keeps states consistent
            self.state = state

        elif (state == hardwareControl_pb2.LightState_Day):
            print(f"Turning {self.name} to day mode!")
            self.mode_relay.gpioObj.off()
            self.enable_relay.gpioObj.on()
            self.state = state

        elif (state == hardwareControl_pb2.LightState_Night):
            print(f"Turning {self.name} to night mode!")
            self.mode_relay.gpioObj.on()
            self.enable_relay.gpioObj.on()
            self.state = state
        else:
            #Unhandled!
            pass

    def turnOff(self):
        self.setState(hardwareControl_pb2.LightState_Off)

    def __str__(self):
        return f"<{self.name}: {self.getStateStr()}>"



class HardwareMap():
    """
        This class exists to map the config json file to an object that holds handles to hw objects
    """

    def setup(self,  configFile):

        print(f"Loading config from {configFile}...\n", flush=True)
        with open(configFile, 'r') as f:
            self.jData = json.load(f)

        RelayObj = namedtuple('RelayObj',['name','gpioObj'])

        print(f"Creating relay objects...\n", flush=True)

        self.relayObjs = []
        for r in self.jData['relays']:
            obj =  RelayObj(name=r['name'], gpioObj=gz.DigitalOutputDevice(pin=r['pin'], active_high=r['active_hi']))
            self.relayObjs.append(obj)

        print(f"Creating light objects...\n", flush=True)

        def lookupRly(name):
            """
            Find first relay in list with given name
            """
            for r in self.relayObjs:
                if r.name == name:
                    return r
            raise NameError(f'No relay with name "{name}" defined.')


        self.lightObjs = []
        for lightInfo in self.jData['lights']:
            enable_relay = lookupRly(lightInfo['enable_relay'])
            mode_relay = lookupRly(lightInfo['mode_relay'])
            obj = Light(lightInfo['name'], enable_relay, mode_relay)
            self.lightObjs.append(obj)

        #Pump stepper
        self.stepper = stepper.StepperMotor(
            self.jData['stepper']['step_pin'],
            self.jData['stepper']['dir_pin'],
            self.jData['stepper']['nen_pin'],
            self.jData['stepper']['ms1_pin'],
            self.jData['stepper']['ms2_pin'],
            self.jData['stepper']['ms3_pin']
            )

        #Thermometer poller
        self.thermometerPoller = sensorpollers.ThermometerPoller(interval_s = self.jData['thermometer']['poll_interval_sec'])

        #PH Sensor Poller
        self.phSensorPoller = sensorpollers.PhSensorPoller(interval_s= self.jData['ph_sensor']['poll_interval_sec'])

hwMap = HardwareMap()

class HardwareControl(hardwareControl_pb2_grpc.HardwareControlServicer):
    """

    """


    def Echo(self, request, context):
        """
            Return the payload back to client as payback
        """
        return hardwareControl_pb2.EchoResponse(payback=request.payload)

    def SetRelayState(self, request, context):
        """
            Set relay state, return nothing
        """
        logging.debug(f"[SERVER] Got relay request: {request.channel} <-- {request.isEngaged}")

        inx = request.channel - 1
        try:
            if (request.isEngaged):
                hwMap.relayObjs[inx].gpioObj.on()
            else:
                hwMap.relayObjs[inx].gpioObj.off()
        except IndexError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid relay channel ({request.channel})")

        return hardwareControl_pb2.Empty()

    def GetRelayStates(self, request, context):
        """
            Return all relay states
        """
        response = hardwareControl_pb2.RelayStates()
        for inx,rly in enumerate(hwMap.relayObjs):
            response.states.append(hardwareControl_pb2.RelayState(channel=(inx+1), isEngaged=rly.gpioObj.is_active))
        return response


    def SetLightState(self, request, context):
        """
            Set light state, return nothing
        """
        logging.info(f"[SERVER] Got light request: {request.lightId} <-- {request.state}")

        try:
            hwMap.lightObjs[request.lightId - 1].changeState(request.state)
        except IndexError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid light channel ({request.lightId})")
            #TODO add handling for bad state enum

        return hardwareControl_pb2.Empty()

    def GetLightStates(self, request, context):
        """
            Return all light states
        """
        response = hardwareControl_pb2.LightStates()
        for inx,obj in enumerate(hwMap.lightObjs):
            response.states.append(hardwareControl_pb2.LightState(lightId=(inx+1), state=obj.getState()))
        return response

    def GetTemperature(self, request, context):
        """
            Get temperature from sensor and return.
            TODO: add timestamp of data collected to message?
        """
        latest_datum = hwMap.thermometerPoller.getLatestDatum()
        return hardwareControl_pb2.Temperature(temperature_degC=latest_datum[1])


    def GetPH(self, request, context):
        """
            Get pH from sensor and return.
        """
        #Get the latest reading from polling thread...
        latest_datum = hwMap.phSensorPoller.getLatestDatum()
        return hardwareControl_pb2.pH(pH=latest_datum[1])

    def MoveStepper(self, request, context):
        """
            Handle command to move stepper motor a certain number of steps
        """
        hwMap.stepper.sendCommand(request.numSteps, isReverse=request.isReverse)

        return hardwareControl_pb2.Empty()




def serve():
    """

    """
    hwMap.setup("./hal/hwconfig.json")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hardwareControl_pb2_grpc.add_HardwareControlServicer_to_server(HardwareControl(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    serve()







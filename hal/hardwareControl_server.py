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

import hardwareControl_pb2
import hardwareControl_pb2_grpc

import gpiozero as gz
import os

#Pinout - TODO, move to config?
#relay_gpio_map = ['GPIO5','GPIO6','GPIO13','GPIO16','GPIO19','GPIO20','GPIO21','GPIO26'] #GPIOxx pins per Raspi Conventoin
#relay_gpio_objs = [gz.DigitalOutputDevice(pin=p, active_high=False) for p in relay_gpio_map]

#To do, this mapping needs to also link to relay obj(s)
#
# lightStates = 2*[hardwareControl_pb2.LightState_Off]
class HardwareMap():
    """
        This class exists to map the config json file to an object that holds handles to hw objects
    """

    def __init__(self, configFile):

        print(f"Loading config from {configFile}...\n", flush=True)
        with open(configFile, 'r') as f:
            self.jData = json.load(f)

        RelayObj = namedtuple('RelayObj',['name','gpioObj'])
        LightObj = namedtuple('LightObj',['name', 'enable_relay', 'mode_relay', 'state']) #TODO - turn into full object

        print(f"Creating relay objects...\n", flush=True)

        self.relayObjs = []
        for r in self.jData['relays']:
            obj =  RelayObj(name=r['name'], gpioObj=gz.DigitalOutputDevice(pin=r['pin'], active_high=r['active_hi']))
            self.relayObjs.append(obj)

        print(f"Creating light objects...\n", flush=True)
        self.lightObjs = []
        for lightInfo in self.jData['lights']:
            enable_relay = None
            mode_relay = None # look these up from config
            obj = LightObj(name=lightInfo['name'], enable_relay=enable_relay, mode_relay=mode_relay, state=hardwareControl_pb2.LightState_Off)
            self.lightObjs.append(obj)

print(os.getcwd())
hwMap = HardwareMap("./hal/hwconfig.json")


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
        print(f"[SERVER] Got relay request: {request.channel} <-- {request.isEngaged}", flush=True)

        inx = request.channel - 1
        if (0 <= inx < len(hwMap.relayObjs)):
            if (request.isEngaged):
                hwMap.relayObjs[inx].gpioObj.on()
            else:
                hwMap.relayObjs[inx].gpioObj.off()
        else:
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

    def GetTemperature(self, request, context):
        """
            Get temperature from sensor and return.
        """
        #TODO Should actually ready from sensor. For now, just return constant.
        return hardwareControl_pb2.Temperature(temperature_degC=20.0)

    def SetLightState(self, request, context):
        """
            Set light state, return nothing
        """
        print(f"[SERVER] Got light request: {request.lightId} <-- {request.state}", flush=True)

        inx = request.lightId - 1
        if (0 <= inx < len(hwMap.lightObjs)):
            #hwMap.lightObjs[inx].state = request.state
            #TODO: this need to be more complex to trigger the proper relays
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)

        else:
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
            response.states.append(hardwareControl_pb2.LightState(lightId=(inx+1), state=obj.state))
        return response

def serve():
    """

    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hardwareControl_pb2_grpc.add_HardwareControlServicer_to_server(HardwareControl(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()







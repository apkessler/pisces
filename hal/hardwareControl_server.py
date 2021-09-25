#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Server for RasPisces Hardware Abstraction Layer Servicer (HAL)
#
#

from concurrent import futures
import logging
import grpc

import hardwareControl_pb2
import hardwareControl_pb2_grpc

import gpiozero as gz


#Pinout - TODO, move to config?
relay_gpio_map = ['GPIO5','GPIO6','GPIO13','GPIO16','GPIO19','GPIO20','GPIO21','GPIO26'] #GPIOxx pins per Raspi Conventoin
relay_gpio_objs = [gz.DigitalOutputDevice(pin=p, active_high=False) for p in relay_gpio_map]

#To do, this mapping needs to also link to relay obj(s)
lightStates = 2*[hardwareControl_pb2.LightState_Off]

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
        if (0 <= inx < len(relay_gpio_objs)):
            if (request.isEngaged):
                relay_gpio_objs[inx].on()
            else:
                relay_gpio_objs[inx].off()
        else:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid relay channel ({request.channel})")

        return hardwareControl_pb2.Empty()

    def GetRelayStates(self, request, context):
        """
            Return all relay states
        """
        response = hardwareControl_pb2.RelayStates()
        for inx,rly in enumerate(relay_gpio_objs):
            response.states.append(hardwareControl_pb2.RelayState(channel=(inx+1), isEngaged=rly.is_active))
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
        if (0 <= inx < len(lightStates)):
            lightStates[inx] = request.state

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
        for inx,obj in enumerate(lightStates):
            response.states.append(hardwareControl_pb2.LightState(lightId=(inx+1), state=obj))
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







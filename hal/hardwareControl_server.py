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

#For now, this represents the hardware state
relay_states = 5*[False]


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
        ## TODO: Needs to actually write to GPIO
        print(f"[SERVER] Got relay request: {request.channel} <-- {request.isEngaged}")
        relay_states[request.channel] = request.isEngaged
        return hardwareControl_pb2.Empty()

    def GetRelayStates(self, request, context):
        """
            Return all relay states
        """
        response = hardwareControl_pb2.RelayStates()
        for i in range(len(relay_states)):
            response.states.append(hardwareControl_pb2.RelayState(channel=i, isEngaged=relay_states[i]))
        return response

    def GetTemperature(self, request, context):
        """
            Get temperature from sensor and return.
        """
        #TODO Should actually ready from sensor. For now, just return constant.
        return hardwareControl_pb2.Temperature(temperature_degC=20.0)

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







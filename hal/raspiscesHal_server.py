#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Server for RasPisces Hardware Abstraction Layer Servicer (HAL)
#
#

from concurrent import futures
import logging
import grpc

import raspiscesHal_pb2
import raspiscesHal_pb2_grpc

class HAL(raspiscesHal_pb2_grpc.RaspiscesHalServiceServicer):
    """

    """

    def Echo(self, request, context):
        """
            Return the payload back to client as payback
        """
        return raspiscesHal_pb2.EchoResponse(payback=request.payload)

def serve():
    """

    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    raspiscesHal_pb2_grpc.add_RaspiscesHalServiceServicer_to_server(HAL(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()







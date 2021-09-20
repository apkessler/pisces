#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Client for Raspisces Hardware Abstraction Layer Servicer (HAL)
#
#

import logging
import grpc

import raspiscesHal_pb2
import raspiscesHal_pb2_grpc


def run():
    """

    """
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = raspiscesHal_pb2_grpc.RaspiscesHalServiceStub(channel)
        response = stub.Echo(raspiscesHal_pb2.EchoRequest(payload='Test123'))
    print(f"Echo returned: {response.payback}")

if __name__ == '__main__':
    logging.basicConfig()
    run()







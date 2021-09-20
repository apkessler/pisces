#!/bin/bash

#TODO: turn this into a makefile
python -m grpc_tools.protoc -I./protodefs/ --python_out=. --grpc_python_out=. ./protodefs/hardwareControl.proto

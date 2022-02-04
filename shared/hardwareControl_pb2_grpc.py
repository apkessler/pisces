# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import hardwareControl_pb2 as hardwareControl__pb2


class HardwareControlStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Echo = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/Echo',
                request_serializer=hardwareControl__pb2.EchoRequest.SerializeToString,
                response_deserializer=hardwareControl__pb2.EchoResponse.FromString,
                )
        self.SetRelayState = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/SetRelayState',
                request_serializer=hardwareControl__pb2.RelayState.SerializeToString,
                response_deserializer=hardwareControl__pb2.Empty.FromString,
                )
        self.GetRelayStates = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/GetRelayStates',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.RelayStates.FromString,
                )
        self.GetTemperature = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/GetTemperature',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.Temperature.FromString,
                )
        self.SetLightState = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/SetLightState',
                request_serializer=hardwareControl__pb2.LightState.SerializeToString,
                response_deserializer=hardwareControl__pb2.Empty.FromString,
                )
        self.GetLightStates = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/GetLightStates',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.LightStates.FromString,
                )
        self.GetPH = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/GetPH',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.pH.FromString,
                )
        self.MoveStepper = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/MoveStepper',
                request_serializer=hardwareControl__pb2.StepperCommand.SerializeToString,
                response_deserializer=hardwareControl__pb2.Empty.FromString,
                )
        self.StopStepper = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/StopStepper',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.Empty.FromString,
                )
        self.IsStepperActive = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/IsStepperActive',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.StepperState.FromString,
                )
        self.SetScope = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/SetScope',
                request_serializer=hardwareControl__pb2.Scope.SerializeToString,
                response_deserializer=hardwareControl__pb2.Empty.FromString,
                )
        self.SetPHSampleTime = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/SetPHSampleTime',
                request_serializer=hardwareControl__pb2.SampleTime.SerializeToString,
                response_deserializer=hardwareControl__pb2.Empty.FromString,
                )
        self.GetPHSampleTime = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/GetPHSampleTime',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.SampleTime.FromString,
                )
        self.SetTemperatureSampleTime = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/SetTemperatureSampleTime',
                request_serializer=hardwareControl__pb2.SampleTime.SerializeToString,
                response_deserializer=hardwareControl__pb2.Empty.FromString,
                )
        self.GetTemperatureSampleTime = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/GetTemperatureSampleTime',
                request_serializer=hardwareControl__pb2.Empty.SerializeToString,
                response_deserializer=hardwareControl__pb2.SampleTime.FromString,
                )
        self.SendPHCommand = channel.unary_unary(
                '/hardwarecontrol.HardwareControl/SendPHCommand',
                request_serializer=hardwareControl__pb2.PHCommand.SerializeToString,
                response_deserializer=hardwareControl__pb2.PHResponse.FromString,
                )


class HardwareControlServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Echo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetRelayState(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetRelayStates(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetTemperature(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetLightState(self, request, context):
        """Should these be in a different service?
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetLightStates(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPH(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def MoveStepper(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StopStepper(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def IsStepperActive(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetScope(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetPHSampleTime(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPHSampleTime(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetTemperatureSampleTime(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetTemperatureSampleTime(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendPHCommand(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_HardwareControlServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Echo': grpc.unary_unary_rpc_method_handler(
                    servicer.Echo,
                    request_deserializer=hardwareControl__pb2.EchoRequest.FromString,
                    response_serializer=hardwareControl__pb2.EchoResponse.SerializeToString,
            ),
            'SetRelayState': grpc.unary_unary_rpc_method_handler(
                    servicer.SetRelayState,
                    request_deserializer=hardwareControl__pb2.RelayState.FromString,
                    response_serializer=hardwareControl__pb2.Empty.SerializeToString,
            ),
            'GetRelayStates': grpc.unary_unary_rpc_method_handler(
                    servicer.GetRelayStates,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.RelayStates.SerializeToString,
            ),
            'GetTemperature': grpc.unary_unary_rpc_method_handler(
                    servicer.GetTemperature,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.Temperature.SerializeToString,
            ),
            'SetLightState': grpc.unary_unary_rpc_method_handler(
                    servicer.SetLightState,
                    request_deserializer=hardwareControl__pb2.LightState.FromString,
                    response_serializer=hardwareControl__pb2.Empty.SerializeToString,
            ),
            'GetLightStates': grpc.unary_unary_rpc_method_handler(
                    servicer.GetLightStates,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.LightStates.SerializeToString,
            ),
            'GetPH': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPH,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.pH.SerializeToString,
            ),
            'MoveStepper': grpc.unary_unary_rpc_method_handler(
                    servicer.MoveStepper,
                    request_deserializer=hardwareControl__pb2.StepperCommand.FromString,
                    response_serializer=hardwareControl__pb2.Empty.SerializeToString,
            ),
            'StopStepper': grpc.unary_unary_rpc_method_handler(
                    servicer.StopStepper,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.Empty.SerializeToString,
            ),
            'IsStepperActive': grpc.unary_unary_rpc_method_handler(
                    servicer.IsStepperActive,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.StepperState.SerializeToString,
            ),
            'SetScope': grpc.unary_unary_rpc_method_handler(
                    servicer.SetScope,
                    request_deserializer=hardwareControl__pb2.Scope.FromString,
                    response_serializer=hardwareControl__pb2.Empty.SerializeToString,
            ),
            'SetPHSampleTime': grpc.unary_unary_rpc_method_handler(
                    servicer.SetPHSampleTime,
                    request_deserializer=hardwareControl__pb2.SampleTime.FromString,
                    response_serializer=hardwareControl__pb2.Empty.SerializeToString,
            ),
            'GetPHSampleTime': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPHSampleTime,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.SampleTime.SerializeToString,
            ),
            'SetTemperatureSampleTime': grpc.unary_unary_rpc_method_handler(
                    servicer.SetTemperatureSampleTime,
                    request_deserializer=hardwareControl__pb2.SampleTime.FromString,
                    response_serializer=hardwareControl__pb2.Empty.SerializeToString,
            ),
            'GetTemperatureSampleTime': grpc.unary_unary_rpc_method_handler(
                    servicer.GetTemperatureSampleTime,
                    request_deserializer=hardwareControl__pb2.Empty.FromString,
                    response_serializer=hardwareControl__pb2.SampleTime.SerializeToString,
            ),
            'SendPHCommand': grpc.unary_unary_rpc_method_handler(
                    servicer.SendPHCommand,
                    request_deserializer=hardwareControl__pb2.PHCommand.FromString,
                    response_serializer=hardwareControl__pb2.PHResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'hardwarecontrol.HardwareControl', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class HardwareControl(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Echo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/Echo',
            hardwareControl__pb2.EchoRequest.SerializeToString,
            hardwareControl__pb2.EchoResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetRelayState(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/SetRelayState',
            hardwareControl__pb2.RelayState.SerializeToString,
            hardwareControl__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetRelayStates(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/GetRelayStates',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.RelayStates.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetTemperature(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/GetTemperature',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.Temperature.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetLightState(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/SetLightState',
            hardwareControl__pb2.LightState.SerializeToString,
            hardwareControl__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetLightStates(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/GetLightStates',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.LightStates.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetPH(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/GetPH',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.pH.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def MoveStepper(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/MoveStepper',
            hardwareControl__pb2.StepperCommand.SerializeToString,
            hardwareControl__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StopStepper(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/StopStepper',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def IsStepperActive(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/IsStepperActive',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.StepperState.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetScope(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/SetScope',
            hardwareControl__pb2.Scope.SerializeToString,
            hardwareControl__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetPHSampleTime(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/SetPHSampleTime',
            hardwareControl__pb2.SampleTime.SerializeToString,
            hardwareControl__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetPHSampleTime(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/GetPHSampleTime',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.SampleTime.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetTemperatureSampleTime(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/SetTemperatureSampleTime',
            hardwareControl__pb2.SampleTime.SerializeToString,
            hardwareControl__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetTemperatureSampleTime(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/GetTemperatureSampleTime',
            hardwareControl__pb2.Empty.SerializeToString,
            hardwareControl__pb2.SampleTime.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendPHCommand(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/hardwarecontrol.HardwareControl/SendPHCommand',
            hardwareControl__pb2.PHCommand.SerializeToString,
            hardwareControl__pb2.PHResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

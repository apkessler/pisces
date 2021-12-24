PY=python

PROTO_LOCATION=build

build: protodefs/hardwareControl.proto
	$(PY) -m grpc_tools.protoc -I./protodefs/ --python_out=. --grpc_python_out=. ./protodefs/hardwareControl.proto


clean:
	echo "cleaning"

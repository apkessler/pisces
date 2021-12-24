PY=python3

PROTO_LOCATION=shared

PROTO_FILE=./hal/protodefs/hardwareControl.proto

protos: $(PROTO_FILE)
	mkdir $(PROTO_LOCATION)
	$(PY) -m grpc_tools.protoc -I./hal/protodefs/ --python_out=./$(PROTO_LOCATION) --grpc_python_out=./$(PROTO_LOCATION) $(PROTO_FILE)


clean:
	rm -rf $(PROTO_LOCATION)


install:
	echo "Install?"
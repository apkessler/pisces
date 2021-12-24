PY=python3

PROTO_LOCATION=shared

#TODO: make this a list?
PROTO_FILE=./hal/protodefs/hardwareControl.proto

protos: $(PROTO_FILE)
	mkdir $(PROTO_LOCATION)
	$(PY) -m grpc_tools.protoc -I./hal/protodefs/ --python_out=./$(PROTO_LOCATION) --grpc_python_out=./$(PROTO_LOCATION) $(PROTO_FILE)


clean:
	rm -rf $(PROTO_LOCATION)


install:
	echo "Install?"
	#add shared location to python path?
	#add and enable services
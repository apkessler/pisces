PY=python3

BUILD_PATH=./build

BUILD_SETTINGS=$(BUILD_PATH)/settings
BUILD_SHARED=$(BUILD_PATH)/shared
BUILD_BIN=$(BUILD_PATH)/bin

PROTO_LOCATION=$(BUILD_SHARED)

#Build env strucure
# pisces-deploy
# |
# +-- shared (grpc files, client)
# +-- settings (json, yaml)
# +-- bin
#     +-- gui.py
#	  +-- hwControl_server.py
#     +-- scheduler.py
#	  +-- dispense.py

#TODO: make this a list?
PROTO_FILE=./hal/protodefs/hardwareControl.proto

all: clean build

protos: $(PROTO_FILE)
	mkdir -p $(PROTO_LOCATION)
	$(PY) -m grpc_tools.protoc -I./hal/protodefs/ --python_out=./$(PROTO_LOCATION) --grpc_python_out=./$(PROTO_LOCATION) $(PROTO_FILE)


clean:
	rm -rf $(BUILD_PATH)

build: protos
	echo "Creating build directory..."
	mkdir -p $(BUILD_PATH)
	mkdir -p $(BUILD_SHARED)
	mkdir -p $(BUILD_SETTINGS)
	mkdir -p $(BUILD_BIN)
	mkdir -p $(BUILD_PATH)/logs

	echo "Copying files..."
#   Move settings files over (better way to do this?)
	cp hal/settings/*		$(BUILD_SETTINGS)
	cp scheduler/settings/* $(BUILD_SETTINGS)
	cp gui/settings/*		$(BUILD_SETTINGS)
	cp dispense/settings/*	$(BUILD_SETTINGS)

#	Move support files over
	cp hal/lib/*		$(BUILD_SHARED)
	cp hal/client/*		$(BUILD_SHARED)
	cp dispense/*.py 	$(BUILD_SHARED)

# 	Move executables over
	cp gui/gui.py				$(BUILD_BIN)
	cp hal/hwcontrol_server.py 	$(BUILD_BIN)
	cp dispense/dispense.py		$(BUILD_BIN)
	cp scheduler/scheduler.py 	$(BUILD_BIN)
	cp scripts/*				$(BUILD_BIN)

	echo "Done!"

install:
	echo "Install?"
	cp services/* ~/.config/systemd/user
	#add shared location to python path?
	#add and enable services
PY=python3

BUILD_PATH=./build

BUILD_SETTINGS=$(BUILD_PATH)/settings
BUILD_SHARED=shared
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
PROTOS_DIR=./protodefs
PYTHON_OUT_DIR=./shared

all: clean build

.PHONY: protos
protos:
	$(PY) -m grpc_tools.protoc -I$(PROTOS_DIR) --python_out=./$(PYTHON_OUT_DIR) --grpc_python_out=./$(PYTHON_OUT_DIR) $(PROTOS_DIR)/*.proto


install:
	echo "Install?"
	cp services/* ~/.config/systemd/user
	systemctl --user daemon-reload
	#add shared location to python path?

	#add to cron tab (deletes any existing entries)
	echo "0 * * * * PYTHONPATH=/home/pi/Repositories/pisces/shared python3 /home/pi/Repositories/pisces/shared/record_stats.py" >> tempcron
	crontab tempcron
	rm tempcron
.PHONY: start_all
start_all:
	systemctl --user start hwcontrol.service
	sleep 1
	systemctl --user start scheduler.service
	sleep 1
	systemctl --user start gui.service


.PHONY: stop_all
stop_all:
	systemctl --user stop gui.service
	systemctl --user stop scheduler.service
	systemctl --user stop hwcontrol.service
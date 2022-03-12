PY=python3


#TODO: make this a list?
PROTOS_DIR=./protodefs
PYTHON_OUT_DIR=./shared

all: clean build

.PHONY: protos
protos:
	$(PY) -m grpc_tools.protoc -I$(PROTOS_DIR) --python_out=./$(PYTHON_OUT_DIR) --grpc_python_out=./$(PYTHON_OUT_DIR) $(PROTOS_DIR)/*.proto


.PHONY: install
install:


	echo "Install"
	#python3 -m pip install -r requirements.txt

	cp services/* ~/.config/systemd/user
	systemctl --user daemon-reload
	#add shared location to python path?

	#add to cron tab (deletes any existing entries)
	echo "0 * * * * PYTHONPATH=/home/pi/Repositories/pisces/shared python3 /home/pi/Repositories/pisces/shared/record_stats.py /home/pi/Repositories/pisces/data/telemetry.csv" >> tempcron
	crontab tempcron
	rm tempcron

	systemctl --user enable hwcontrol.service
	systemctl --user enable gui.service



.PHONY: start_all
start_all:
	systemctl --user restart hwcontrol.service
    #This should make gui restart also

.PHONY: stop_all
stop_all:
	systemctl --user stop gui.service
	systemctl --user stop hwcontrol.service

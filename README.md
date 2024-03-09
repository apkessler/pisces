# RaspberryPisces
Aquarium automation via Raspberry Pi 🐟 🐠

# Installation

Clone repository on target.

```bash
git clone https://github.com/apkessler/pisces.git
cd pisces
git pull

python3 -m pip install -r requirements.txt
sudo apt install python3-numpy
sudo apt install python3-pandas
sudo apt install python3-matplotlib
make install
```

`make install` will install and enable the necessary systemd services, and install the cron job that calls the
telemetry updating script.

## Getting updates
Pull latest from Git, and rerun `make install`

# Other notes
The `grpcio` package has been tricky to install on RPi for whatever reason...

## Configuration Files

### schedule.json

The file `data/schedule.json` has the the interesting, user editable schedule information about when lights/outlets turn
on/off. When the GUI is started, it looks to see if `data/schedule.json` exists. If it does not, it copies the default
settings file (`gui/schedule.default.json`) to `/data`. Users can edit the contents of `schedule.json` through the GUI
itself.

### gui.json
The file `gui.json` has some configuration options for the GUI, mostly about how the Graphicing windows are drawn. There
is currently no mechansim (or use case) for editing the `gui.json` file from within the GUI.

### hwcontrol_server.json

The `hwcontrol_server.json` file has information about the hardware and pinout. Specifically:
- which GPIOs drive which relays
- which GPIOs drive the stepper motor
- which relays driver with light/outlet
- polling intervals for thermometer & pH sensor

There is no expected use-case where this file should be edited during deployment.

## Running in a simulated enviornment
If you want to do development on a system without the actual sensor hardware, you can run the hwcontrol service in
"mock" mode (`-m`). This will post randomly generate temperature and ph data. GPIOs will also be simulated.

If you're running on a Linux system that supports systemd, you just add `-m` to the ExecStart line in `hwcontrol.service`.
If you're developing on a Windows/Mac (without systemd), you can just manually start the hwcontrol service in mock mode
(and start the GUI as well, without the `--fullscreen` flag.)
)
```bash
cd pisces
PYTHONPATH=shared/ python hwcontrol/hwcontrol.py -m
PYTHONPATH=shared/ python gui/gui.py
```

### Developing on MacOS
Running the GUI on MacOS, you may get the error:
```
    import _tkinter # If this fails your Python may not be configured for Tk
ModuleNotFoundError: No module named '_tkinter'
```
Install python-tk by doing:
```brew install python-tk```
(you will need to have homebrew installed first).

## Local AP Mode

The script `scripts/enable_AP.sh` will turn the Raspberry Pi into a local WiFi access point. That is, rather then connect
to an existing WiFi network, it will broadcast its *own* WiFi network that another computer can connect to.
This can be a convenient way to communicate with the instrument when a local network is not available. However, note that in
this mode it is a local network only, and will not have connection to the wider internet.

To disable local AP mode, run `scripts/disable_AP.sh`.

## Checking internal Raspberry Pi Temperature
```bash
$ /opt/vc/bin/vcgencmd measure_temp
```

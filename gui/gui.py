#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Main executable for Pisces GUI.

"""

### Imports

# Standard imports
import os
import socket
import logging
import datetime
import threading

# 3rd party imports
import tkinter as tk
import grpc
import json

# Custom imports
import hardwareControl_pb2
import hardwareControl_pb2_grpc
from hwcontrol_client import HardwareControlClient
from dispense import dispense


##### Globals ####
fontTuple = ('Arial', 15)

hwCntrl = None #Global stub, because its easiest
jData = None #config data


### Helper functions

def get_ip():
    """
        Get IP address of this device, return as string.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def sys_call(cmd):
    import subprocess
    output = ""
    try:
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
    except FileNotFoundError:
        output = f"Could not execute sys call: '{cmd}'"
    finally:
        logging.info(output)


def reboot_pi():
    logging.info("restarting the Pi")
    sys_call("/usr/bin/sudo /sbin/shutdown -r now")

# modular function to shutdown Pi
def shutdown_pi():
    logging.info("shutting down the Pi")
    sys_call("/usr/bin/sudo /sbin/shutdown -h now")


### TKinter Stuff

class Window(object):
    """Generic window object. Do not instantiate directly.

    Parameters
    ----------
    object : [type]
        [description]
    """

    def __init__(self, title, handle):
        self.master = handle
        self.master.wm_geometry("640x480")
        self.master.title(title)
        if (jData['fullscreen']):
            self.master.attributes('-fullscreen', True)


    def dummy(self):
        pass

    def drawButtonGrid(self, buttonMap):
        """Build the standard grid of buttons

        Parameters
        ----------
        buttonMap : [type]
            [description]
        """
        self.buttons = []
        frame = tk.Frame(self.master)
        frame.place(in_=self.master, anchor='c', relx=0.5, rely=0.55)
        for inx, bInfo in enumerate(buttonMap):
            f = tk.Frame(frame, width=200, height=200, padx=10, pady=10) #make a frame where button goes
            if (type(bInfo[0]) is str):
                b = tk.Button(f, text=bInfo[0], font=fontTuple, command=bInfo[1])
            else:
                b = tk.Button(f, textvariable=bInfo[0], font=fontTuple, command=bInfo[1])

            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight = 1)
            f.grid_propagate(0)

            f.grid(row = int(inx/3), column=inx%3)
            b.grid(sticky="NWSE")
            self.buttons.append(b)



class MainWindow(Window):
    """The main window (shown on launch). Should only be one of these.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    def __init__(self, root):
        super().__init__("Main Window", root)
        hwCntrl.setScope() #Reset scope to make sure schedule is running
        self.lightToggleModes = ['Schedule', 'All On', 'All Blue', 'All Off']
        self.currentLightToggleModeInx = 0

        self.lightModeText = tk.StringVar()
        self.lightModeText.set("Lights:\n"+self.lightToggleModes[self.currentLightToggleModeInx])

        self.timeText = tk.StringVar()
        self.updateTimestamp()
        tk.Label(root, textvariable=self.timeText, font=('Arial',18)).place(x=475, y=15)


        self.tempText = tk.StringVar()
        self.tempText.set(f"Temperature\n???°F")

        self.phText = tk.StringVar()
        self.phText.set(f"pH\n???")


        buttons = [
            [self.lightModeText, self.toggle_lights],
            [self.tempText, lambda: TemperaturePage()],
            [self.phText, lambda: PhPage()],
            ["Manual\nFertilizer", lambda: ManualFertilizerPage()],
            ["Settings", lambda: SettingsPage()]
        ]

        self.drawButtonGrid(buttons)


        #After we're done setting everything up...
        self.refresh_data()

    def updateTimestamp(self):
        now = datetime.datetime.now()
        self.timeText.set(now.strftime("%I:%M:%S %p"))

    def toggle_lights(self):
        self.currentLightToggleModeInx = (self.currentLightToggleModeInx + 1) % len(self.lightToggleModes)


        myScope = 'gui'
        newMode = self.lightToggleModes[self.currentLightToggleModeInx]
        self.lightModeText.set("Lights:\n"+newMode)
        logging.info(f"Toggled to mode {newMode}")
        if (newMode == 'Schedule'):
            hwCntrl.setScope()
        elif (newMode == 'All On'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2,3]:
                hwCntrl.setLightState(lightId, hardwareControl_pb2.LightState_Day, scope=myScope)

        elif (newMode == 'All Blue'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2]:
                hwCntrl.setLightState(lightId, hardwareControl_pb2.LightState_Night, scope=myScope)
            hwCntrl.setLightState(3, hardwareControl_pb2.LightState_Day, scope=myScope) #Keep gro lights on


        elif (newMode == 'All Off'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2,3]:
                hwCntrl.setLightState(lightId, hardwareControl_pb2.LightState_Off, scope=myScope)


    def refresh_data(self):
        self.updateTimestamp()

        #Update all things that need updating

        #Update the temperature reading
        temp_degC = hwCntrl.getTemperature_degC()
        temp_degF = (temp_degC * 9.0) / 5.0 + 32.0
        self.tempText.set(f"Temperature\n{temp_degF:0.2f}°F")

        #Update the pH Reading
        ph = hwCntrl.getPH()
        self.phText.set(f"pH\n{ph:0.2f}")

        self.master.after(1000, self.refresh_data)

    def quit(self):
        self.root.quit()



class Subwindow(Window):
    """Generic Subwindow class. Make an inherited class from this for a custom subwindow.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    def __init__(self, title):
        super().__init__(title, tk.Toplevel())

        self.master.grab_set()

        btn = tk.Button(self.master, text="Back", font=fontTuple, width=9, height=2, bg='#ff5733', command=self.exit)
        btn.place(x=450, y=10)

    def exit(self):
        self.master.destroy()
        self.master.update()


class TemperaturePage(Subwindow):

    def __init__(self):
        super().__init__("Temperature Info")

        btn = tk.Button(self.master, text="Temp Stuff")
        btn.pack()

class SettingsPage(Subwindow):

    def __init__(self):
        super().__init__("Settings")

        buttons = [
            ["Reboot\nBox", reboot_pi],
            ["Aquarium\nLights", self.dummy],
            ["Grow Lights", self.dummy],
            ["Fertilizer", self.dummy],
            ["Calibrate pH", self.dummy],
            ["System Settings", lambda: SystemSettingsPage()]
        ]

        self.drawButtonGrid(buttons)



class SystemSettingsPage(Subwindow):

    def __init__(self):
        super().__init__("System Settings")

        tk.Label(self.master, text=f"IP Address: {get_ip()}", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady= 5)
        tk.Label(self.master, text=f"", font=("Arial", 12)).grid(row=2, column=0)
        tk.Label(self.master, text=f"", font=("Arial", 12)).grid(row=3, column=0)


        buttons = [
            ["About", self.dummy],
            ["Shutdown\nBox", shutdown_pi],
            ["Exit GUI", self.quitGui],
            ["Network Info", self.dummy],
            ["Set Time", self.dummy],
            ["Restore\nDefaults", self.dummy]
        ]

        self.drawButtonGrid(buttons)


    def quitGui(self):
        """Close this entire GUI program
        """
        self.master.quit()


class PhPage(Subwindow):

    def __init__(self):
        super().__init__("pH Info")


class ManualFertilizerPage(Subwindow):

    def __init__(self):
        super().__init__("Fertilizer Info")

        buttons = [
            ["Dispense\n3mL",lambda: self.dispenseInThread(3)],
            ["Dispense\n10mL", lambda: self.dispenseInThread(10)],
            ["Hold to\ndispense\ncontinuously", None],
            ["Timer\nSettings", lambda:SettingsPage()]
        ]
        self.drawButtonGrid(buttons)

        #Link the hold to dispense button to press/release callbacks
        self.buttons[2].bind("<ButtonPress>", self.on_press)
        self.buttons[2].bind("<ButtonRelease>", self.on_release)

    def on_press(self, event):
        self.dispense_stop_event = threading.Event()
        self.dispenseThread = threading.Thread(target=dispense, args=(hwCntrl, 100, self.dispense_stop_event), daemon=True)
        self.dispenseThread.start()


    def on_release(self, event):
        if (self.dispenseThread.is_alive()):
            self.dispense_stop_event.set()
            self.dispenseThread.join()
            logging.info("Dispense thread killed")
        else:
            self.dispenseThread.join()
            logging.info("Dispense thread already dead")


    def dispenseInThread(self, volume_ml):
        stop_event = threading.Event()
        self.thread = threading.Thread(target=dispense, args=(hwCntrl, volume_ml, stop_event), daemon=True)
        self.thread.start()
        self.thread.join()


if __name__ == "__main__":
    #Load the config file
    with open(os.path.join( 'settings','gui.json'), 'r') as jsonfile:
        jData = json.load(jsonfile)

    logging.basicConfig(
        filename=jData['log_name'],
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().setLevel(jData['log_level'])
    logging.info("--------- GUI RESTART-------------")

    with grpc.insecure_channel(jData['server']) as channel:
        hwCntrl = HardwareControlClient(channel)
        hwCntrl.echo()
        root = tk.Tk()
        main = MainWindow(root)
        root.mainloop()

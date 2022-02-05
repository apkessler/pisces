#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Main executable for Pisces GUI.

"""

### Imports

# Standard imports
import os
import socket
import datetime
import threading

# 3rd party imports
import tkinter as tk
from graphviz import Graph
import grpc
import json

import pandas as pd
from matplotlib.figure import Figure


from loguru import logger

import numpy as np #Don't need?
import matplotlib as plt
from matplotlib.figure import (Figure, )
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler



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
        logger.info(output)


def reboot_pi():
    logger.info("restarting the Pi")
    sys_call("/usr/bin/sudo /sbin/shutdown -r now")

# modular function to shutdown Pi
def shutdown_pi():
    logger.info("shutting down the Pi")
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
            [self.tempText, lambda: GraphPage('Temperature (F)')],
            [self.phText, lambda: GraphPage('pH')],
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
        logger.info(f"Toggled to mode {newMode}")

        if (newMode == 'Schedule'):
            hwCntrl.setScope() #Release scope, return to normal schedule

        elif (newMode == 'All On'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2,3]:
                hwCntrl.setLightColor(lightId, 'white', scope=myScope)

        elif (newMode == 'All Blue'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2]:
                hwCntrl.setLightColor(lightId, 'blue', scope=myScope)
            hwCntrl.setLightColor(3, 'white', scope=myScope) #Keep gro lights on


        elif (newMode == 'All Off'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2,3]:
                hwCntrl.setLightColor(lightId, 'off', scope=myScope)


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

    def __init__(self, title, exit_button_text="Back"):
        super().__init__(title, tk.Toplevel())

        self.master.grab_set()

        btn = tk.Button(self.master, text=exit_button_text, font=fontTuple, width=9, height=2, bg='#ff5733', command=self.exit)
        btn.place(x=450, y=10)

    def exit(self):
        self.master.destroy()
        self.master.update()


class GraphPage(Subwindow):

    def __init__(self, field:str):
        super().__init__(field)

        #Read in the dataframe and parse timestamp strings to datetime
        self.df = pd.read_csv(jData['telemetry_file'], parse_dates=["Timestamp"])

        #Set the index to timestamp column so we can index by it
        self.df.set_index('Timestamp', inplace=True)

        #Pull the safe hi/lo bounds to plot horz lines from config file
        if (field == 'Temperature (F)'):
            self.safe_ylim_hi = jData['temp_hi_degF']
            self.safe_ylim_lo = jData['temp_lo_degF']
        elif (field == 'pH'):
            self.safe_ylim_hi = jData['ph_hi']
            self.safe_ylim_lo = jData['ph_lo']
        else:
            raise Exception(f"Bad Graph Type {field}")


        self.fig = Figure(figsize=(5,4), dpi = 100)
        self.ax = self.fig.add_subplot()

        self.field = field

        top = tk.Frame(self.master)
        bottom = tk.Frame(self.master)
        top.pack(side=tk.TOP)
        bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


        self.canvas = FigureCanvasTkAgg(self.fig, master=bottom) # A tk.DrawingArea
        self.canvas.draw()


        #By default, show the last week of data
        self.initial_now = datetime.datetime.now()
        one_week = datetime.timedelta(days=7)
        self.plot_data(self.initial_now - one_week, self.initial_now)

        # pack_toolbar=False will make it easier to use a layout manager later on.
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master, pack_toolbar=False)
        self.toolbar.update()

        def show_previous_week():
            try:
                self.initial_now -= one_week
                self.plot_data(self.initial_now - one_week, self.initial_now)
            except IndexError:
                logger.info("Cannot go back any further!")
                self.initial_now += one_week #Undo what we just tried...

        def show_next_week():
            self.initial_now += one_week
            now = datetime.datetime.now()
            if (self.initial_now > now):
                self.initial_now = now
            self.plot_data(self.initial_now - one_week, self.initial_now)

        def show_this_week():
            self.initial_now = datetime.datetime.now()
            self.plot_data(self.initial_now - one_week, self.initial_now)

        def show_all_time():
            self.plot_data(self.df.index.min(), self.df.index.max())

        #We need to manually recreate the Back button since it got wiped by the matplotlib canvas
        back_btn = tk.Button(self.master, text="Back", font=fontTuple, width=9, height=2, bg='#ff5733', command=self.exit)
        last_week_btn = tk.Button(self.master, text="Back\n 1 Week", command=show_previous_week,  font=fontTuple, width=9, height=2)
        next_week_btn = tk.Button(self.master, text="Forward\n1 Week", command=show_next_week,  font=fontTuple, width=9, height=2)
        this_week_btn = tk.Button(self.master, text="This\nWeek", command=show_this_week,  font=fontTuple, width=9, height=2)

        all_time_btn = tk.Button(self.master, text="All\nTime", command=show_all_time,  font=fontTuple, width=9, height=2)


        # Packing order is important. Widgets are processed sequentially and if there
        # is no space left, because the window is too small, they are not displayed.
        # The canvas is rather flexible in its size, so we pack it last which makes
        # sure the UI controls are displayed as long as possible.

        last_week_btn.pack(in_=top, side=tk.LEFT)
        next_week_btn.pack(in_=top, side=tk.LEFT)

        this_week_btn.pack(in_=top, side=tk.LEFT)
        all_time_btn.pack(in_=top, side=tk.LEFT)

        back_btn.pack(in_=top, side=tk.LEFT)
        #self.toolbar.pack(in_=bottom, side=tk.BOTTOM, fill=tk.X)

        self.canvas.get_tk_widget().pack(in_=bottom, side=tk.TOP, fill=tk.BOTH, expand=1)

    def plot_data(self, start_time:datetime.datetime, end_time: datetime.datetime):

        self.ax.cla()
        self.df[start_time: end_time].plot(y=[self.field], ax=self.ax)
        self.ax.hlines(y=[self.safe_ylim_lo, self.safe_ylim_hi], xmin=[start_time], xmax=[end_time], colors='red', linestyles='--', lw=1)

        self.ax.set_ylabel(self.field)
        self.ax.set_xlabel('')
        self.fig.subplots_adjust(bottom=0.166)
        self.canvas.draw()


class SettingsPage(Subwindow):

    def __init__(self):
        super().__init__("Settings")

        buttons = [
            ["Reboot\nBox", reboot_pi],
            ["Aquarium\nLights", self.dummy],
            ["Grow Lights", self.dummy],
            ["Fertilizer", self.dummy],
            ["Calibrate pH", lambda: CalibratePhStartPage()],
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
            logger.info("Dispense thread killed")
        else:
            self.dispenseThread.join()
            logger.info("Dispense thread already dead")


    def dispenseInThread(self, volume_ml):
        stop_event = threading.Event()
        self.thread = threading.Thread(target=dispense, args=(hwCntrl, volume_ml, stop_event), daemon=True)
        self.thread.start()
        self.thread.join()


class CalibratePhStartPage(Subwindow):

    def __init__(self):
        super().__init__("pH Sensor Calibration")

        msg = "To calibrate the pH sensor, you will need all three\nof the calibration solutions (pH=7.0, 4.0, 10.0)." + \
               "\n\nIf you've got those ready, go ahead\nand hit the START button!" + \
                "\n\nWARNING: Starting this process will\nerase any existing calibration."

        tk.Label(self.master, text=msg, font=('Arial',18), justify=tk.LEFT).place(x=50, y=100)

        btn = tk.Button(self.master, text="Start!", font=fontTuple, width=15, height=4, bg='#00ff00', command=self.run_sequence)
        btn.place(x=250, y=330)

        #Start this now to give the default sleep period time to end (up to 1min)
        hwCntrl.setPhSensorSampleTime(1000) #Speed up ph sensor sample time

    def exit(self):
        '''
            Override in case of abort to set sample time back
        '''
        #return sample rate to default
        hwCntrl.setPhSensorSampleTime(0)
        super().exit()

    def run_sequence(self):

        CalibratePhProcessPage()
        super().exit() #Don't call the local version to avoid resetting sample time


class CalibratePhDonePage(Subwindow):

    def __init__(self):
        super().__init__("pH Sensor Calibration")

        msg = "pH Sensor calibration complete! Woohoo!"

        tk.Label(self.master, text=msg, font=('Arial',18), justify=tk.LEFT).place(x=50, y=100)

        btn = tk.Button(self.master, text="Done", font=fontTuple, width=15, height=6, bg='#00ff00', command=self.exit)
        btn.place(x=250, y=250)



class CalibratePhProcessPage(Subwindow):

    def __init__(self):
        super().__init__(f"pH Sensor Calibration", exit_button_text="Abort")

        self.index = 0
        self.sequence = [
            ('7.0', 'Cal,mid,7.00'),
            ('4.0', 'Cal,low,4.00'),
            ('10.0', 'Cal,high,10.00')
        ]

        self.titleText = tk.StringVar()
        self.titleText.set(f"Calibrate @ pH={self.sequence[self.index][0]}")
        tk.Label(self.master, textvar=self.titleText, font=('Arial',22), justify=tk.LEFT).place(x=20, y=20)

        self.line1Text = tk.StringVar()
        self.line1Text.set(f"1. Get the {self.sequence[self.index][0]} calibration solution.\n")
        tk.Label(self.master, textvar=self.line1Text, font=('Arial',18), justify=tk.LEFT).place(x=50, y=100)

        msg2 = "2. Briefly rinse off the probe.\n"
        msg2 += "3. Cut off the top of the calibration solution pouch.\n"
        msg2 += "4. Place the pH probe inside the pouch.\n"
        msg2 += "5. Wait for the pH reading to stabilize (1-2min).\nWhen it does, hit \"Next\".\n"

        tk.Label(self.master, text=msg2, font=('Arial',18), justify=tk.LEFT).place(x=50, y=125)

        self.phText = tk.StringVar()
        self.phText.set(f"pH\n???")
        tk.Label(self.master, textvariable=self.phText, font=('Arial',22)).place(x=100, y=300)

        self.errorText = tk.StringVar()
        tk.Label(self.master, textvar=self.errorText, font=('Arial',18), fg='#f00', justify=tk.LEFT).place(x=320, y=420)

        btn = tk.Button(self.master, text="Next", font=fontTuple, width=12, height=4, bg='#00ff00', command=self.save_calibration)
        btn.place(x=350, y=300)

        self.refresh_data()

    def refresh_data(self):

        #Update the pH Reading
        ph = hwCntrl.getPH()
        self.phText.set(f"pH\n{ph:0.2f}")

        self.master.after(1000, self.refresh_data)

    def save_calibration(self):
        '''
            TODO: Send the save calibration command to sensor...
        '''
        cmd = self.sequence[self.index][1]
        logger.info(f"Sending save cal command: {cmd}")

        result = hwCntrl.sendPhSensorCommand(cmd)
        if (result == '1'):
            logger.info(f"calibration command success!")
        else:
            logger.error(f"calibration command failed ({result})")
            self.errorText.set("Error! Please retry.")
            return # Bail now, and retry

        self.index += 1
        if (self.index >= len(self.sequence)):
            CalibratePhDonePage()
            self.exit()
        else:
            self.titleText.set(f"Calibrate @ pH={self.sequence[self.index][0]}")
            self.line1Text.set(f"1. Get the {self.sequence[self.index][0]} calibration solution.\n")
            self.errorText.set("")

    def exit(self):
        '''
            Override in case of abort to set sample time back
        '''
        #return sample rate to default
        hwCntrl.setPhSensorSampleTime(0) #Return to default
        super().exit()


if __name__ == "__main__":

    logger.add('gui.log', format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", level="INFO", rotation="10MB")
    logger.info("--------- GUI RESTART-------------")

    #Load the config file
    with open(os.path.join(os.path.dirname(__file__), 'gui.json'), 'r') as jsonfile:
        jData = json.load(jsonfile)


    with grpc.insecure_channel(jData['server']) as channel:
        hwCntrl = HardwareControlClient(channel)
        try:
            hwCntrl.echo()
            root = tk.Tk()
            main = MainWindow(root)
            root.mainloop()
        except grpc.RpcError as rpc_error:
            logger.error(f"Unable to connect to server! {rpc_error.code()}")
            exit()





#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Main executable for Pisces GUI.

"""

### Imports

# Standard imports
import argparse
import os
import datetime
import threading
import shutil

# 3rd party imports
import tkinter as tk
import grpc
import json

import pandas as pd

from typing import Tuple
from loguru import logger

import matplotlib as plt
from matplotlib.figure import (Figure, )
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

# Custom imports
from hwcontrol_client import HardwareControlClient
from dispense_client import dispense
from helpers import *
from windows import (Window, Subwindow, ErrorPromptPage, fontTuple)
from system_settings import (SystemSettingsPage, RebootPromptPage)
from timer_settings import (AquariumLightsSettingsPage, OutletSettingsPage)
import scheduler

##### Globals ####

hwCntrl = None #Global stub, because its easiest
jData = None #config data

class MainWindow(Window):
    """The main window (shown on launch). Should only be one of these.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    def __init__(self, root, fullscreen):
        super().__init__("Main Window", root, fullscreen)
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

        self.the_scheduler = scheduler.Scheduler(hwCntrl)

        if (not os.path.exists(SCHEDULE_CONFIG_FILE)):
            #Copy the default config file!
            logger.info('No schedule json file found - copying default file.')
            shutil.copyfile(SCHEDULE_CONFIG_DEFAULT_FILE, SCHEDULE_CONFIG_FILE)


        with open(SCHEDULE_CONFIG_FILE, 'r') as configfile:
            sch_jData= json.load(configfile)
        self.the_scheduler.build_light_timers(sch_jData["light_schedules"])
        self.the_scheduler.build_outlet_timers(sch_jData["outlet_schedules"])

        for event in sch_jData["events"]:
            self.the_scheduler.add_event(event["name"], event['trigger_time_hhmm'], lambda:DispensingCapturePage(volume_mL=event['volume_mL']))

        buttons = [
            {'text':self.lightModeText,     'callback': self.toggle_lights},
            {'text':self.tempText,          'callback': lambda: GraphPage('Temperature (F)')},
            {'text':self.phText,            'callback': lambda: GraphPage('pH')},
            {'text':"Manual\nFertilizer",   'callback': lambda: ManualFertilizerPage()},
            {'text':"Settings",             'callback': lambda: SettingsPage()}
        ]

        self.drawButtonGrid(buttons)


        #After we're done setting everything up...
        self.update_scheduler()
        self.refresh_data()

    def updateTimestamp(self):
        now = datetime.datetime.now()
        self.timeText.set(now.strftime("%I:%M:%S %p"))

    def toggle_lights(self):
        self.currentLightToggleModeInx = (self.currentLightToggleModeInx + 1) % len(self.lightToggleModes)

        newMode = self.lightToggleModes[self.currentLightToggleModeInx]
        self.lightModeText.set("Lights:\n"+newMode)
        logger.info(f"Toggled to mode {newMode}")

        if (newMode == 'Schedule'):
            self.the_scheduler.resume_timers(['tank_lights', 'outlet1'])

        elif (newMode == 'All On'):
            self.the_scheduler.disable_timers(['tank_lights', 'outlet1'])
            for lightId in [1,2,3]:
                hwCntrl.setLightColor(lightId, 'white')

        elif (newMode == 'All Blue'):
            self.the_scheduler.disable_timers(['tank_lights', 'outlet1'])
            for lightId in [1,2]:
                hwCntrl.setLightColor(lightId, 'blue')
            hwCntrl.setLightColor(3, 'white') #Keep gro lights on

        elif (newMode == 'All Off'):
            self.the_scheduler.disable_timers(['tank_lights', 'outlet1'])
            for lightId in [1,2,3]:
                hwCntrl.setLightColor(lightId, 'off')

    def update_scheduler(self):

        logger.debug("Scheduler update")
        self.the_scheduler.update(datetime.datetime.now())
        self.master.after(30*1000, self.update_scheduler)

    def refresh_data(self):
        self.updateTimestamp()

        #Update all things that need updating

        #Update the temperature reading
        temp_degC = hwCntrl.getTemperature_degC()
        temp_degF = (temp_degC * 9.0) / 5.0 + 32.0
        self.tempText.set(f"Temperature\n{temp_degF:0.1f}°F")

        #Update the pH Reading
        ph = hwCntrl.getPH()
        self.phText.set(f"pH\n{ph:0.1f}")
        #Uncomment next line to make pH button change color based on pH
        #self.buttons[2].configure(bg=ph_to_color(ph))

        self.master.after(1000, self.refresh_data)

    def quit(self):
        self.root.quit()


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

        if (self.safe_ylim_lo != None and self.safe_ylim_hi != None):
            self.ax.hlines(y=[self.safe_ylim_lo, self.safe_ylim_hi], xmin=[start_time], xmax=[end_time], colors='red', linestyles='--', lw=1)

        self.ax.set_ylabel(self.field)
        self.ax.set_xlabel('')
        self.fig.subplots_adjust(bottom=0.166)
        self.canvas.draw()


class SettingsPage(Subwindow):

    def __init__(self):
        super().__init__("Settings")

        buttons = [
            {'text':"Reboot\nBox",      'callback': reboot_pi},
            {'text':"Aquarium\nLights", 'callback': lambda: AquariumLightsSettingsPage()},
            {'text':"Outlet\nTimers",      'callback': lambda: OutletSettingsPage()},
            {'text':"Fertilizer\nSettings", 'callback': lambda: FertilizerSettingsPage()},
            {'text':"Calibrate pH",     'callback': lambda: CalibratePhStartPage()},
            {'text':"System Settings",  'callback': lambda: SystemSettingsPage()}
        ]

        self.drawButtonGrid(buttons)

class FertilizerSettingsPage(Subwindow):
    ''' Page for adjusting Fertilizer Settings '''
    def __init__(self):
        super().__init__("Fertilizer Settings", draw_exit_button=False)

        #Load the scheduler json file
        this_dir = os.path.dirname(__file__)
        with open(SCHEDULE_CONFIG_FILE, 'r') as jsonfile:
            self.config_data = json.load(jsonfile)


        schedules = self.config_data['events']

        self.this_event = None
        for schedule in schedules:
            if (schedule['name'] == 'DailyFertilizer'):
                self.this_event = schedule

        if (self.this_event == None):
            logger.error("Unable to find DailyFertilizer object in scheduler.json")

        big_font = ('Arial', 20)

        time_setting_frame = tk.LabelFrame(self.master, text="Daily Dispense Settings", font=fontTuple)

        tk.Label(self.master, text="Changes will take effect on next system reboot.", font=('Arial', 16)).grid(row=4, column=0)

        time_setting_frame.grid(row=1, column =0, sticky='ew', padx=10, pady=10)

        tk.Label(time_setting_frame, text="Dispense Time:", font=big_font).grid(row=1, column=0)
        tk.Label(time_setting_frame, text="Volume (mL):", font=big_font).grid(row=2, column=0)


        self.time_selector = TimeSelector(time_setting_frame, self.this_event['trigger_time_hhmm'])
        self.time_selector.frame.grid(row=1, column=1)

        self.volume_var = tk.IntVar()
        self.volume_var.set(self.this_event['volume_mL'])
        tk.Spinbox( time_setting_frame,
                    from_=0,
                    to=50,
                    wrap=True,
                    textvariable=self.volume_var,
                    width=4,
                    font=('Courier', 30),
                    justify=tk.CENTER).grid(row=2, column=1)

        btn = tk.Button(self.master, text="Cancel", font=fontTuple, width=12, height=4, bg='#ff5733', command=self.exit)
        btn.grid(row=1, column=2, padx=10, pady=10)
        btn = tk.Button(self.master, text="Save", font=fontTuple, width=12, height=4, bg='#00ff00', command=self.save_settings)
        btn.grid(row=2, column=2, padx=10, pady=10)

    def save_settings(self):

        #Pull out the requisite info, and write it back to config
        self.this_event["trigger_time_hhmm"] = self.time_selector.get_hhmm()
        self.this_event['volume_mL'] = int(self.volume_var.get())

        #Grab the tank light on time for reference
        for schedule in self.config_data['light_schedules']:
            if (schedule['name'] == 'TankLights'):
                self.tank_light_schedule = schedule

        def hhmmToDatetime(hhmm) -> datetime.datetime:
            hh = int(hhmm/100)
            mm = hhmm - hh*100
            return datetime.datetime.combine(datetime.date.today(), datetime.time(hour=hh, minute=mm))

        this_time =  hhmmToDatetime(self.this_event["trigger_time_hhmm"])
        tank_on_time = hhmmToDatetime(self.tank_light_schedule['sunrise_hhmm'])

        if (this_time + datetime.timedelta(minutes=10) > tank_on_time):
            # We enforce this constraint to avoid weird edge cases where the dispense's tasks messing with light settings
            # gets messed up by a night -> day or day -> night transition. We could try to fix this with a scope param,
            # then there's more weird edges cases if the lights are in a manual mode...
            ErrorPromptPage(f"Fertilizer dispense time must be at least\n10min before tank light on time ({tank_on_time.time()})")
        else:
            logger.info("Writing new settings to file...")
            with open(SCHEDULE_CONFIG_FILE, 'w') as jsonfile:
                json.dump(self.config_data, jsonfile, indent=4)

            self.exit()
            RebootPromptPage()


class ManualFertilizerPage(Subwindow):

    def __init__(self):
        super().__init__("Fertilizer Info")

        buttons = [
            {'text': "Dispense\n3mL",   'callback': lambda: self.dispenseInThread(3)},
            {'text': "Dispense\n10mL",  'callback': lambda: self.dispenseInThread(10)},
            {'text': "Hold to\ndispense\ncontinuously", 'callback': None}, #This button has special binding
            {'text': "Fertilizer\nSettings", 'callback': lambda:FertilizerSettingsPage()}
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


class DispensingCapturePage(Subwindow):
    ''' A Page to capture the UI when a scheduled dispense is in progress'''
    def __init__(self, volume_mL):
        super().__init__("Dispense in Progress", draw_exit_button=False)

        buttons = [
            {'text': "Abort",     'callback': self.abort, 'color':'#ff5733'}
        ]

        self.drawButtonGrid(buttons)

        tk.Label(self.master,
        text=f"Scheduled fertilizer dispense ({volume_mL}mL) in progress.",
        font=('Arial', 20)).pack(side=tk.TOP, pady=75)
        logger.info('Starting dispense thread')
        self.dispense_stop_event = threading.Event()
        self.dispenseThread = threading.Thread(target=dispense, args=(hwCntrl, volume_mL, self.dispense_stop_event), daemon=True)
        self.dispenseThread.start()
        self.master.after(1000, self.check_if_dispense_done)


    def check_if_dispense_done(self):
        '''Callback function called at 1Hz to check if dispensing done. If so, self destruct'''
        if (self.dispenseThread.is_alive()):
            logger.info('Dispense thread still running...')
            self.master.after(1000, self.check_if_dispense_done)
        else:
            logger.info('Dispense thread done!')
            self.dispenseThread.join()
            self.exit()



    def abort(self):
        if (self.dispenseThread.is_alive()):
            self.dispense_stop_event.set()
            self.dispenseThread.join()
            logger.info("Dispense thread killed")
        else:
            self.dispenseThread.join()
            logger.info("Dispense thread already dead")
        self.exit()


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
            ('7.0', 'Cal,mid,7.00', 'Midpoint'),
            ('4.0', 'Cal,low,4.00','Lowpoint'),
            ('10.0', 'Cal,high,10.00', 'Highpoint')
        ]

        self.titleText = tk.StringVar()
        self.titleText.set(f"{self.sequence[self.index][2]} calibration @ pH={self.sequence[self.index][0]}")
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
            self.titleText.set(f"{self.sequence[self.index][2]} calibration @ pH={self.sequence[self.index][0]}")
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

    logger.add(os.path.join(os.path.dirname(__file__), '../data/gui.log'),
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10MB")
    logger.info("--------- GUI RESTART-------------")

    parser = argparse.ArgumentParser("GUI Runner")
    parser.add_argument("--fullscreen", "-f", action='store_true', default=False, help="Run in fullscreen mode")

    args = parser.parse_args()

    #Load the config file
    with open(os.path.join(os.path.dirname(__file__), 'gui.json'), 'r') as jsonfile:
        jData = json.load(jsonfile)


    with grpc.insecure_channel(jData['server']) as channel:
        hwCntrl = HardwareControlClient(channel)
        try:
            root = tk.Tk()
            main = MainWindow(root, args.fullscreen)
            root.mainloop()
            logger.error("Tkinter mainloop terminated!")
        except grpc.RpcError as rpc_error:
            logger.error(f"Unable to connect to server! {rpc_error.code()}")
            exit()





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
import time
import textwrap

# 3rd party imports
import tkinter as tk
import grpc
import json
from loguru import logger

# Custom imports
from hwcontrol_client import HardwareControlClient
from dispense_client import dispense
from helpers import *
from windows import (Window, Subwindow, ErrorPromptPage, ConfirmPromptPage, fontTuple, activity_kick)
from system_settings import (SystemSettingsPage, RelaunchPromptPage, NetworkSettingsPage)
from timer_settings import (AquariumLightsSettingsPage, OutletSettingsPage)
from graph_pages import GraphPage
import scheduler


##### Globals ####

hwCntrl = None #Global stub, because its easiest
jData = None #config data
MAX_VOLUME_ML = 15

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
        tk.Label(root, textvariable=self.timeText, font=('Arial',25)).place(x=425, y=15)


        self.temp_value = tk.StringVar()
        self.ph_value = tk.StringVar()
        self.warning_text = tk.StringVar()
        self.ph_value_for_lock_screen = tk.StringVar()
        self.lock_screen_ph_text = tk.StringVar()

        self.the_scheduler = scheduler.Scheduler(hwCntrl)


        # self.unlock_img = tk.PhotoImage(file=os.path.join(ICON_PATH, "unlock_icon.png")).subsample(10,10)

        self.ph_img = tk.PhotoImage(file=os.path.join(ICON_PATH, "ph_icon.png")).subsample(3,3)
        self.temperature_img = tk.PhotoImage(file=os.path.join(ICON_PATH, "temperature_icon.png")).subsample(3,3)

        SCALE = 6
        self.ph_img_small = tk.PhotoImage(file=os.path.join(ICON_PATH, "ph_icon.png")).subsample(SCALE,SCALE)
        self.temperature_img_small = tk.PhotoImage(file=os.path.join(ICON_PATH, "temperature_icon.png")).subsample(SCALE,SCALE)
        self.settings_img_small = tk.PhotoImage(file=os.path.join(ICON_PATH, "settings_icon.png")).subsample(SCALE,SCALE)
        self.fert_img_small = tk.PhotoImage(file=os.path.join(ICON_PATH, "peristaltic-pump-2.png")).subsample(9,9)

        #self.light_img_small = tk.PhotoImage(file=os.path.join(ICON_PATH, "light_icon.png")).subsample(SCALE,SCALE)

        self.light_white = tk.PhotoImage(file=os.path.join(ICON_PATH, "light_white.png")).subsample(SCALE,SCALE)
        self.light_blue = tk.PhotoImage(file=os.path.join(ICON_PATH, "light_blue.png")).subsample(SCALE,SCALE)
        self.light_timer = tk.PhotoImage(file=os.path.join(ICON_PATH, "light_timer.png")).subsample(SCALE,SCALE)
        self.light_off = tk.PhotoImage(file=os.path.join(ICON_PATH, "light_off.png")).subsample(SCALE,SCALE)



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
            {'text':self.lightModeText, 'callback': self.toggle_lights,                           'image':self.light_timer},
            {'text':self.temp_value,    'callback': lambda: GraphPage('Temperature (F)', jData),  'image':self.temperature_img_small},
            {'text':self.ph_value,      'callback': lambda: GraphPage('pH',jData),                'image':self.ph_img_small},
            {'text':"Peristaltic Pump", 'callback': lambda: ManualDispensePage(),                 'image':self.fert_img_small},
            {'text':"Settings",         'callback': lambda: SettingsPage(),                       'image':self.settings_img_small},
            {'text': self.warning_text, 'callback': lambda: (),                    'image':None}
        ]

        self.drawButtonGrid(buttons)


        #After we're done setting everything up...
        self.scheduler_count = 0
        self.update_scheduler()
        self.refresh_data()

        #Setup the activity watchdog for screen lock
        self.set_activity_timeout(jData['lock_time_s'])
        self.set_activity_expiration_callback(self.activity_expiration)
        self.kick_activity_watchdog()

        self.draw_lock_button()

        #Configure for entire window class
        self.set_wifi_callback(lambda:NetworkSettingsPage())
        self.set_get_wifi_state_func(is_wifi_on)

        self.draw_wifi_indicator(as_button=True)




    def activity_expiration(self):
        ''' This is the function what will be called when the activity watchdog expires.
            If LockWindow is not already in existence, close all subwindows (return to home screen) and lock the screen.
            Otherwise, just kill the timer. '''
        if (Window.activity_timer != None):
            #In case this was called manually, stop the timer
            Window.activity_timer.cancel()

        logger.debug("MainWindow activity expiration!")

        if (LockScreen.is_locked()):
            logger.debug("LockScreen already exists, not opening new one.")
            # LockScreen.grab_set() #Make this screen front most layer

        else:
            Subwindow.destroy_all()
            LockScreen(self)


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
            self.buttons[0].configure(image=self.light_timer)

        elif (newMode == 'All On'):
            self.buttons[0].configure(image=self.light_white)
            self.the_scheduler.disable_timers(['tank_lights', 'outlet1'])
            for lightId in [1,2,3]:
                hwCntrl.setLightColor(lightId, 'white')

        elif (newMode == 'All Blue'):
            self.buttons[0].configure(image=self.light_blue)
            self.the_scheduler.disable_timers(['tank_lights', 'outlet1'])
            for lightId in [1,2]:
                hwCntrl.setLightColor(lightId, 'blue')
            hwCntrl.setLightColor(3, 'white') #Keep gro lights on

        elif (newMode == 'All Off'):
            self.buttons[0].configure(image=self.light_off)
            self.the_scheduler.disable_timers(['tank_lights', 'outlet1'])
            for lightId in [1,2,3]:
                hwCntrl.setLightColor(lightId, 'off')

    def update_scheduler(self):
        ''' Called every 30sec. Makes decisions about what should happen at this time, etc.
        '''
        self.last_scheduler_update_mono_sec = time.monotonic()
        logger.debug(f"Scheduler update")
        self.the_scheduler.update(datetime.datetime.now())


    def refresh_data(self):
        '''Called every 1sec. Updates time, gets fresh pH/Temp readings, and kicks the systemd watchdog.
            Updates scheduler every 30th call.
        '''

        #Kick the systemd watchdog. This is to catch the tkinter timers getting messed up due to a system time change,
        #likely triggered by an NTP sync
        notify_systemd_watchdog()


        self.updateTimestamp()

        #By doing this in this function, it is tied to the systemd watchdog. And if the displayed time is
        #updating, then the scheduler is alive!
        self.scheduler_count +=1
        if (self.scheduler_count >= 30):
            self.update_scheduler()
            self.scheduler_count = 0

        #Update the temperature reading
        temp_degC = hwCntrl.getTemperature_degC()
        temp_degF = (temp_degC * 9.0) / 5.0 + 32.0
        self.temp_value.set(f"{temp_degF:0.1f}°F")

        #Update the pH Reading
        ph = hwCntrl.getPH()
        self.ph_value.set(f"{ph:0.1f}")
        self.ph_value_for_lock_screen.set(f"{ph:0.1f}")
        #Uncomment next line to make pH button change color based on pH
        #self.buttons[2].configure(bg=ph_to_color(ph))

        self.master.after(1000, self.refresh_data)

        #Check calibration age
        pch = PhCalibrationHelper()

        lock_screen_msg, main_window_msg = get_ph_warning_message(
                ph,
                last_cal_date=pch.get_latest_ph_calibration_date(),
                time_now = datetime.datetime.now(),
            )
        self.warning_text.set("Warning!\n" + "\n".join(textwrap.wrap(main_window_msg, width=20)))

        if lock_screen_msg == PhMessages.MSG_RECALIBRATION_REQUIRED:
            self.ph_value_for_lock_screen.set("") #Don't show a pH value

        self.lock_screen_ph_text.set("\n".join(textwrap.wrap(lock_screen_msg, width=20)))


    def quit(self):
        self.root.quit()

class LockScreen(Subwindow):

    _is_locked = False

    def __init__(self, main_window):
        super().__init__("Lock Screen", draw_exit_button=False, draw_lock_button=False, draw_wifi_indicator=True)
        LockScreen._is_locked = True

        self.lock_img = tk.PhotoImage(file=os.path.join(ICON_PATH, "lock_icon.png")).subsample(10,10)
        b = tk.Button(self.master, image=self.lock_img, command=self.exit)
        b.place(x=20, y=7)
        b.configure(bg='#BBBBBB')

        self.draw_wifi_indicator(as_button=False)

        #Make the frame to put the real time status info
        frame = tk.Frame(self.master)
        frame.place(in_=self.master, anchor='c', relx=0.5, rely=0.55)

        tk.Label(self.master, textvariable=main_window.timeText, font=('Arial',30)).place(x=300, y=50)
        tk.Label(frame, image=main_window.ph_img).grid(row=1,column=2, padx=50)
        tk.Label(frame, image=main_window.temperature_img).grid(row=1,column=1, padx=50)

        tk.Label(frame, textvariable=main_window.temp_value, font=('Arial',35)).grid(row=2,column=1, padx=50)
        tk.Label(frame, textvariable=main_window.ph_value_for_lock_screen, font=('Arial',35)).grid(row=2,column=2, padx=50)

        tk.Label(self.master, textvariable=main_window.lock_screen_ph_text, fg='#f00', font=('Arial',25)).place(x=370, y=380)

    @classmethod
    def is_locked(cls) -> bool:
        return cls._is_locked

    def exit(self):
        '''Override default exit'''
        LockScreen._is_locked = False
        logger.debug("Lock screen destroyed")
        super().exit()






class SettingsPage(Subwindow):

    def __init__(self):
        super().__init__("Settings")

        buttons = [
            {'text':"Reboot\nBox",      'callback': lambda:ConfirmPromptPage("Are you sure you want to reboot?", reboot_pi)},
            {'text':"Aquarium\nLights", 'callback': lambda: AquariumLightsSettingsPage()},
            {'text':"Outlet\nTimers",      'callback': lambda: OutletSettingsPage()},
            {'text':"Peristaltic Pump\nSettings", 'callback': lambda: PeriPumpSettingsPage()},
            {'text':"pH Calibration",     'callback': lambda: CalibratePhStartPage()},
            {'text':"System Settings",  'callback': lambda: SystemSettingsPage()}
        ]

        self.drawButtonGrid(buttons)

class PeriPumpSettingsPage(Subwindow):
    ''' Page for adjusting PeriPump Settings '''
    def __init__(self):
        super().__init__("PeriPump Settings", draw_exit_button=False)

        #Load the scheduler json file
        this_dir = os.path.dirname(__file__)
        with open(SCHEDULE_CONFIG_FILE, 'r') as jsonfile:
            self.config_data = json.load(jsonfile)


        schedules = self.config_data['events']

        self.this_event = None
        for schedule in schedules:
            if (schedule['name'] == 'DailyDispense'):
                self.this_event = schedule

        if (self.this_event == None):
            logger.error("Unable to find DailyDispense object in scheduler.json")

        big_font = ('Arial', 20)

        time_setting_frame = tk.LabelFrame(self.master, text="Daily Dispense Settings", font=fontTuple)

        tk.Label(self.master, text="Changes will take effect on next GUI restart.", font=('Arial', 16)).grid(row=4, column=0)

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
        self.tank_light_schedule = self.config_data['light_schedules']['tank_lights']

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
            ErrorPromptPage(f"Daily dispense time must be at least\n10min before tank light on time ({tank_on_time.time()})")
        elif (self.this_event['volume_mL'] > MAX_VOLUME_ML):
            #We limit this because at longer dispenses seem to cause pump to start skipping?
            ErrorPromptPage(f"Daily dispense volume cannot exceed {MAX_VOLUME_ML}mL")
        else:
            logger.info("Writing new settings to file...")
            with open(SCHEDULE_CONFIG_FILE, 'w') as jsonfile:
                json.dump(self.config_data, jsonfile, indent=4)

            self.exit()
            RelaunchPromptPage()


class ManualDispensePage(Subwindow):

    def __init__(self):
        super().__init__("PeriPump Info")

        buttons = [
            {'text': "Dispense\n1mL",   'callback': lambda: DispensingCapturePage(1, scheduled=False)},
            {'text': "Dispense\n3mL",   'callback': lambda: DispensingCapturePage(3, scheduled=False)},
            {'text': "Dispense\n10mL",  'callback': lambda: DispensingCapturePage(10, scheduled=False)},
            {'text': "Dispense\n15mL", 'callback': lambda: DispensingCapturePage(15, scheduled=False)},
            {'text': "Peristaltic Pump\nSettings", 'callback': lambda:PeriPumpSettingsPage()}
        ]
        self.drawButtonGrid(buttons)


class DispensingCapturePage(Subwindow):
    ''' A Page to capture the UI when a scheduled dispense is in progress'''
    def __init__(self, volume_mL, scheduled=True):
        super().__init__("Dispense in Progress", draw_exit_button=False, draw_lock_button=False)

        buttons = [
            {'text': "Abort",     'callback': self.abort, 'color':'#ff5733'}
        ]

        self.drawButtonGrid(buttons)

        if (scheduled):
            msg = f"Scheduled dispense ({volume_mL}mL) in progress."
        else:
            msg = f"Dispense ({volume_mL}mL) in progress."

        tk.Label(self.master,
        text=msg,
        font=('Arial', 20)).pack(side=tk.TOP, pady=75)
        logger.info('Starting dispense thread')
        self.dispense_stop_event = threading.Event()
        self.dispenseThread = threading.Thread(target=dispense, args=(hwCntrl, volume_mL, self.dispense_stop_event), daemon=True)
        self.dispenseThread.start()
        self.master.after(1000, self.check_if_dispense_done)

    @activity_kick
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
        #If aborted, kill all subwindows (including LockScreen, if relevant) and return to MainPage.
        #This is not the ideal behavior, but a workaround to the fact that if you abort
        #a scheduled dispense, the ordering of windows gets screwed up (the 2nd highest window moves to front?)
        #Anyway, this is a rough workaround for that behavior.
        Subwindow.destroy_all()


class CalibratePhStartPage(Subwindow):

    def __init__(self):
        super().__init__("pH Sensor Calibration")

        msg = "To calibrate the pH sensor, you will need all three\nof the calibration solutions (pH=7.0, 4.0, 10.0)." + \
               "\n\nIf you've got those ready, go ahead\nand hit the START button!" + \
                "\n\nWARNING: Starting this process will erase any existing\ncalibration," +\
                "and disable the screen from locking."

        tk.Label(self.master, text=msg, font=('Arial',18), justify=tk.LEFT).place(x=25, y=100)

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

        pch = PhCalibrationHelper()
        pch.record_calibration(datetime.datetime.now(), {})



class CalibratePhProcessPage(Subwindow):

    def __init__(self):
        super().__init__(f"pH Sensor Calibration", exit_button_text="Abort", draw_lock_button=False)

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

        self.next_btn = tk.Button(self.master, text="Next", font=fontTuple, width=10, height=3, bg='#00ff00', command=self.save_calibration)
        self.next_btn.place(x=200, y=300)

        self.refresh_data()

    @activity_kick
    def refresh_data(self):

        #Update the pH Reading
        ph = hwCntrl.getPH()
        self.phText.set(f"pH\n{ph:0.2f}")

        self.master.after(1000, self.refresh_data)

    @activity_kick
    def save_calibration(self):
        '''
            TODO: Send the save calibration command to sensor...
        '''
        cmd = self.sequence[self.index][1]
        logger.info(f"Sending save cal command: {cmd}")

        result = hwCntrl.sendPhSensorCommand(cmd)
        if (result == '1' or result == ''):
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
            self.next_btn.place(x=200 + int(self.index*150), y=300)

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

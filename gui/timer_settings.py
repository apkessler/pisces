
'''Timer Settings GUI Elements    '''

from helpers import *
from windows import (Subwindow, fontTuple, ErrorPromptPage)
from system_settings import (RebootPromptPage)
import os

SCHEDULE_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'scheduler.json')

class AquariumLightsSettingsPage(Subwindow):
    ''' Page for adjusting Aquarium (Tank) light settings.'''
    def __init__(self):
        super().__init__("Aquarium Light Settings", draw_exit_button=False)

        #Load the scheduler json file
        with open(SCHEDULE_CONFIG_FILE, 'r') as jsonfile:
            self.config_data = json.load(jsonfile)


        schedules = self.config_data['light_schedules']

        self.tank_light_schedule = None
        for schedule in schedules:
            if (schedule['name'] == 'TankLights'):
                self.tank_light_schedule = schedule

        if (self.tank_light_schedule == None):
            logger.error("Unable to find TankLight object in scheduler.json")

        big_font = ('Arial', 20)

        time_setting_frame = tk.LabelFrame(self.master, text="Day/Night Schedule", font=fontTuple)
        eclipse_setting_frame = tk.LabelFrame(self.master, text="Periodic Blue Settings", font=fontTuple)
        tk.Label(self.master, text="Changes will take effect on next system reboot.", font=('Arial', 16)).grid(row=4, column=0)

        time_setting_frame.grid(row=1, column =0, sticky='ew', padx=10, pady=10)
        eclipse_setting_frame.grid(row=2, column =0, sticky='ew', padx=10, pady=10)


        tk.Label(time_setting_frame, text="On Time:", font=big_font).grid(row=1, column=0)
        tk.Label(time_setting_frame, text="Off Time:", font=big_font).grid(row=2, column=0)
        tk.Label(time_setting_frame, text="Blue at night:", font=big_font).grid(row=3, column=0)


        self.sunrise_selector = TimeSelector(time_setting_frame, self.tank_light_schedule['sunrise_hhmm'])
        self.sunrise_selector.frame.grid(row=1, column=1)

        self.sunset_selector = TimeSelector(time_setting_frame, self.tank_light_schedule['sunset_hhmm'])
        self.sunset_selector.frame.grid(row=2, column=1)


        self.blue_at_night_var = tk.StringVar()
        self.blue_at_night_var.set("True" if self.tank_light_schedule['blue_lights_at_night'] else "False")
        OPTIONS = ["True", "False"]
        w = tk.OptionMenu(time_setting_frame, self.blue_at_night_var, *OPTIONS)
        w.config(font=big_font) # set the button font
        menu = eclipse_setting_frame.nametowidget(w.menuname)
        menu.config(font=big_font)  # Set the dropdown menu's font
        w.grid(row=3, column=1, sticky='w')

        tk.Label(eclipse_setting_frame, text="Enabled:", font=big_font).grid(row=1, column=0)
        tk.Label(eclipse_setting_frame, text="Interval (min)", font=big_font).grid(row=2, column=0)
        tk.Label(eclipse_setting_frame, text="Duration (min)", font=big_font, justify=tk.CENTER).grid(row=3, column=0, sticky='w')


        self.period_blue_lights_enabled = tk.StringVar()
        self.period_blue_lights_enabled.set("True" if self.tank_light_schedule['eclipse_enabled'] else "False")
        OPTIONS = ["True", "False"]
        w = tk.OptionMenu(eclipse_setting_frame, self.period_blue_lights_enabled, *OPTIONS)
        w.config(font=big_font) # set the button font
        menu = eclipse_setting_frame.nametowidget(w.menuname)
        menu.config(font=big_font)  # Set the dropdown menu's font
        w.grid(row=1, column=1, sticky='w')

        self.blue_interval_min_var = tk.IntVar()
        self.blue_interval_min_var.set(self.tank_light_schedule['eclipse_frequency_min'])

        self.blue_interval_select = tk.Spinbox(
                        eclipse_setting_frame,
                        from_=0,
                        to=59,
                        wrap=True,
                        textvariable=self.blue_interval_min_var,
                        width=4,
                        font=('Courier', 30),
                        justify=tk.CENTER)
        self.blue_interval_select.grid(row=2, column=1)

        self.blue_duration_min_var = tk.IntVar()
        self.blue_duration_min_var.set(self.tank_light_schedule['eclipse_duration_min'])
        self.blue_duration_select = tk.Spinbox(
                        eclipse_setting_frame,
                        from_=0,
                        to=59,
                        wrap=True,
                        textvariable=self.blue_duration_min_var,
                        width=4,
                        font=('Courier', 30),
                        justify=tk.CENTER)
        self.blue_duration_select.grid(row=3, column=1)

        btn = tk.Button(self.master, text="Cancel", font=fontTuple, width=12, height=4, bg='#ff5733', command=self.exit)
        btn.grid(row=1, column=2, padx=10, pady=10)
        btn = tk.Button(self.master, text="Save", font=fontTuple, width=12, height=4, bg='#00ff00', command=self.save_settings)
        btn.grid(row=2, column=2, padx=10, pady=10)

    def save_settings(self):

        #Pull out the requisite info, and write it back to config
        self.tank_light_schedule["sunrise_hhmm"] = self.sunrise_selector.get_hhmm()
        self.tank_light_schedule["sunset_hhmm"]  = self.sunset_selector.get_hhmm()
        self.tank_light_schedule['blue_lights_at_night'] = True if self.blue_at_night_var.get() == "True" else False

        self.tank_light_schedule['eclipse_enabled'] = True if self.period_blue_lights_enabled.get() == "True" else False

        self.tank_light_schedule['eclipse_frequency_min'] = int(self.blue_interval_min_var.get())
        self.tank_light_schedule['eclipse_duration_min'] = int(self.blue_duration_min_var.get())

        if (self.sunrise_selector.get_hhmm() >= self.sunset_selector.get_hhmm()):
            logger.warning("Bad timing config!")
            ErrorPromptPage("On time must be before Off time!")
        else:
            logger.info("Writing new settings to file...")
            with open(self.path_to_configfile, 'w') as jsonfile:
                json.dump(self.config_data, jsonfile, indent=4)


            self.exit()
            RebootPromptPage()

class GrowLightsSettingsPage(Subwindow):
    ''' Page for adjusting Grow Light Settings '''
    def __init__(self):
        super().__init__("Grow Light Settings", draw_exit_button=False)

        #Load the scheduler json file
        this_dir = os.path.dirname(__file__)
        with open(SCHEDULE_CONFIG_FILE, 'r') as jsonfile:
            self.config_data = json.load(jsonfile)


        schedules = self.config_data['light_schedules']

        self.grow_light_schedule = None
        for schedule in schedules:
            if (schedule['name'] == 'GrowLights'):
                self.grow_light_schedule = schedule

        if (self.grow_light_schedule == None):
            logger.error("Unable to find GrowLight object in scheduler.json")

        big_font = ('Arial', 20)

        time_setting_frame = tk.LabelFrame(self.master, text="Day/Night Schedule", font=fontTuple)

        tk.Label(self.master, text="Changes will take effect on next system reboot.", font=('Arial', 16)).grid(row=4, column=0)

        time_setting_frame.grid(row=1, column =0, sticky='ew', padx=10, pady=10)

        tk.Label(time_setting_frame, text="On Time:", font=big_font).grid(row=1, column=0)
        tk.Label(time_setting_frame, text="Off Time:", font=big_font).grid(row=2, column=0)


        self.sunrise_selector = TimeSelector(time_setting_frame, self.grow_light_schedule['sunrise_hhmm'])
        self.sunrise_selector.frame.grid(row=1, column=1)

        self.sunset_selector = TimeSelector(time_setting_frame, self.grow_light_schedule['sunset_hhmm'])
        self.sunset_selector.frame.grid(row=2, column=1)

        btn = tk.Button(self.master, text="Cancel", font=fontTuple, width=12, height=4, bg='#ff5733', command=self.exit)
        btn.grid(row=1, column=2, padx=10, pady=10)
        btn = tk.Button(self.master, text="Save", font=fontTuple, width=12, height=4, bg='#00ff00', command=self.save_settings)
        btn.grid(row=2, column=2, padx=10, pady=10)

    def save_settings(self):

        #Pull out the requisite info, and write it back to config
        self.grow_light_schedule["sunrise_hhmm"] = self.sunrise_selector.get_hhmm()
        self.grow_light_schedule["sunset_hhmm"]  = self.sunset_selector.get_hhmm()

        if (self.sunrise_selector.get_hhmm() >= self.sunset_selector.get_hhmm()):
            logger.warning("Bad timing config!")
            ErrorPromptPage("On time must be before Off time!")
        else:
            logger.info("Writing new settings to file...")
            with open(SCHEDULE_CONFIG_FILE, 'w') as jsonfile:
                json.dump(self.config_data, jsonfile, indent=4)



            self.exit()
            RebootPromptPage()

class OutletSettingsPage(Subwindow):
    ''' Page for adjusting Outlet 2,3,4 Settings '''
    def __init__(self):
        super().__init__("Outlet Settings", draw_exit_button=False)

        #Load the scheduler json file
        this_dir = os.path.dirname(__file__)
        with open(SCHEDULE_CONFIG_FILE, 'r') as jsonfile:
            self.config_data = json.load(jsonfile)



        rowcounter = 1
        self.enable_selectors = {}
        self.sunrise_selectors = {}
        self.sunset_selectors = {}
        for outlet_name in ["Outlet2", "Outlet3", "Outlet4"]:
            this_sched = self.get_outlet_sched(outlet_name)
            big_font = ('Arial', 20)


            time_setting_frame = tk.LabelFrame(self.master, text=outlet_name, font=fontTuple)
            time_setting_frame.grid(row=rowcounter, column =0, sticky='ew', padx=10, pady=10)
            tk.Label(time_setting_frame, text="On Time:", font=big_font).grid(row=1, column=0)
            tk.Label(time_setting_frame, text="Off Time:", font=big_font).grid(row=2, column=0)

            self.enable_selectors[outlet_name] = tk.StringVar()
            self.enable_selectors[outlet_name].set("Enable" if this_sched['enabled'] else "Disable")
            OPTIONS = ["Enable", "Disable"]
            w = tk.OptionMenu(time_setting_frame, self.enable_selectors[outlet_name], *OPTIONS)
            w.config(font=('Arial', 16)) # set the button font
            menu = time_setting_frame.nametowidget(w.menuname)
            menu.config(font=('Arial', 16))  # Set the dropdown menu's font
            w.grid(row=1, column=2, sticky='w')

            self.sunrise_selectors[outlet_name] = TimeSelector(time_setting_frame, this_sched['sunrise_hhmm'])
            self.sunrise_selectors[outlet_name].frame.grid(row=1, column=1)

            self.sunset_selectors[outlet_name] = TimeSelector(time_setting_frame, this_sched['sunset_hhmm'])
            self.sunset_selectors[outlet_name].frame.grid(row=2, column=1)

            rowcounter+=1

        btn = tk.Button(self.master, text="Cancel", font=fontTuple, width=8, height=4, bg='#ff5733', command=self.exit)
        btn.grid(row=1, column=2, padx=10, pady=10)
        btn = tk.Button(self.master, text="Save", font=fontTuple, width=8, height=4, bg='#00ff00', command=self.save_settings)
        btn.grid(row=2, column=2, padx=10, pady=10)

        tk.Label(self.master, text="Changes will take effect on next system reboot.", font=('Arial', 16)).grid(row=rowcounter, column=0)

    def get_outlet_sched(self, name:str) ->dict:

        for schedule in self.config_data["light_schedules"]:
            if (schedule['name'] == name):
                return schedule

        logger.error(f"Unable to find {name} object in scheduler.json")
        return None


    def save_settings(self):

        #Pull out the requisite info, and write it back to config
        for outlet_name in ["Outlet2", "Outlet3", "Outlet4"]:
            this_sched = self.get_outlet_sched(outlet_name)
            this_sched["enabled"] = self.enable_selectors[outlet_name].get()
            this_sched["sunrise_hhmm"] = self.sunrise_selectors[outlet_name].get_hhmm()
            this_sched["sunset_hhmm"]  = self.sunset_selectors[outlet_name].get_hhmm()

            if (self.sunrise_selectors[outlet_name].get_hhmm() >= self.sunset_selectors[outlet_name].get_hhmm()):
                logger.warning("Bad timing config!")
                ErrorPromptPage("On time must be before Off time!")
                return #This needs to be fixed before doing anything

        #If everything was valid, save to file
        logger.info("Writing new settings to file...")
        with open(SCHEDULE_CONFIG_FILE, 'w') as jsonfile:
            json.dump(self.config_data, jsonfile, indent=4)

        self.exit()
        RebootPromptPage()

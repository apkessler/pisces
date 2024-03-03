
'''Timer Settings GUI Elements    '''

from helpers import *
from windows import (Subwindow, fontTuple, ErrorPromptPage, activity_kick)
from system_settings import (RelaunchPromptPage)
import os

class AquariumLightsSettingsPage(Subwindow):
    ''' Page for adjusting Aquarium (Tank) light settings.'''
    def __init__(self):
        super().__init__("Aquarium Light Settings", draw_exit_button=False)

        #Load the scheduler json file
        with open(SCHEDULE_CONFIG_FILE, 'r') as jsonfile:
            self.config_data = json.load(jsonfile)

        self.tank_light_schedule = self.config_data['light_schedules']['tank_lights']

        big_font = ('Arial', 20)

        time_setting_frame = tk.LabelFrame(self.master, text="Light Schedule", font=fontTuple)
        eclipse_setting_frame = tk.LabelFrame(self.master, text="Blue Cycle Settings", font=fontTuple)
        enabled_setting_frame = tk.LabelFrame(self.master, text="Lights Enabled", font=fontTuple)
        tk.Label(self.master, text=wrap_text("Some changes may not take effect until the next GUI relaunch.", width=25), font=('Arial', 16)).grid(row=3, column=1)

        time_setting_frame.grid(row=1, column =0, sticky='ew', padx=10, pady=10)
        eclipse_setting_frame.grid(row=2, column =0, sticky='ew', padx=10, pady=10)
        enabled_setting_frame.grid(row=3, column =0, sticky='ew', padx=10, pady=10)


        ## Light Schedule Frame
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
        self.blue_at_night_var.trace("w", self.widget_update)


        ## Blue Cycle Settings Frame
        tk.Label(eclipse_setting_frame, text="Enabled:", font=big_font).grid(row=1, column=0)
        tk.Label(eclipse_setting_frame, text="Blue (min):", font=big_font).grid(row=2, column=0)
        tk.Label(eclipse_setting_frame, text="White (min):", font=big_font, justify=tk.CENTER).grid(row=3, column=0, sticky='w')


        self.period_blue_lights_enabled = tk.StringVar()
        self.period_blue_lights_enabled.set("True" if self.tank_light_schedule['eclipse_enabled'] else "False")
        OPTIONS = ["True", "False"]
        w = tk.OptionMenu(eclipse_setting_frame, self.period_blue_lights_enabled, *OPTIONS)
        w.config(font=big_font) # set the button font
        menu = eclipse_setting_frame.nametowidget(w.menuname)
        menu.config(font=big_font)  # Set the dropdown menu's font
        w.grid(row=1, column=1, sticky='w')
        self.period_blue_lights_enabled.trace("w", self.widget_update)

        self.blue_length_min_var = tk.IntVar()

        total_period_m = self.tank_light_schedule['eclipse_frequency_min']
        blue_period_m = self.tank_light_schedule['eclipse_duration_min']
        white_period_m = total_period_m - blue_period_m
        self.blue_length_min_var.set(blue_period_m)


        self.blue_length_select = tk.Spinbox(
                        eclipse_setting_frame,
                        from_=0,
                        to=59,
                        wrap=True,
                        textvariable=self.blue_length_min_var,
                        width=4,
                        font=('Courier', 30),
                        justify=tk.CENTER,
                        command=self.widget_update)
        self.blue_length_select.grid(row=2, column=1)

        self.white_length_min_var = tk.IntVar()
        self.white_length_min_var.set(white_period_m)
        self.white_duration_select = tk.Spinbox(
                        eclipse_setting_frame,
                        from_=0,
                        to=59,
                        wrap=True,
                        textvariable=self.white_length_min_var,
                        width=4,
                        font=('Courier', 30),
                        justify=tk.CENTER,
                        command=self.widget_update)
        self.white_duration_select.grid(row=3, column=1)

        ## Lights Enabled Frame
        tk.Label(enabled_setting_frame, text="Light1", font=big_font).grid(row=1, column=0)
        tk.Label(enabled_setting_frame, text="Light2", font=big_font).grid(row=2, column=0)
        tk.Label(enabled_setting_frame, text="White", font=big_font).grid(row=0, column=1)
        tk.Label(enabled_setting_frame, text="Blue", font=big_font).grid(row=0, column=2)
        self.enable_vars = {i: {'white_enabled': tk.IntVar(), 'blue_enabled': tk.IntVar()} for i in [1,2]}


        CHECKBOX_SIZE = 24 #This is ~ the size of the checkmark image /6
        self.on_image =  tk.PhotoImage(file=os.path.join(ICON_PATH, "checkmark.png")).subsample(6,6)
        self.off_image = tk.PhotoImage(width=CHECKBOX_SIZE, height=CHECKBOX_SIZE)
        self.off_image.put(("white",), to=(0, 0, CHECKBOX_SIZE - 1, CHECKBOX_SIZE - 1))


        for l_id in self.enable_vars:
            for c_id, c_var in self.enable_vars[l_id].items():
                tk.Checkbutton(
                    enabled_setting_frame,
                    variable= c_var,
                    image=self.off_image,
                    selectimage=self.on_image,
                    indicatoron=False,
                    onvalue=1,
                    offvalue=0,
                ).grid(row=l_id,column=1 if c_id == "white_enabled" else 2)

                c_var.set(1 if self.tank_light_schedule['lights'][f"TankLight{l_id}"][c_id] else 0)

        tk.Label(enabled_setting_frame,
                 text=wrap_text("You can enable or disable specific colors on each light. If it is unchecked here, it will not turn on as part of the schedule.", width=25),
                 font=('Arial', 13)
                 ).grid(row=1, rowspan=2, column=3, padx=10, pady=10)

        ## Buttons
        btn = tk.Button(self.master, text="Cancel", font=fontTuple, width=12, height=4, bg='#ff5733', command=self.exit)
        btn.grid(row=1, column=1, padx=10, pady=10)
        btn = tk.Button(self.master, text="Save", font=fontTuple, width=12, height=4, bg='#00ff00', command=self.save_settings)
        btn.grid(row=2, column=1, padx=10, pady=10)

    @activity_kick
    def widget_update(self, *args, **kwargs):
        #This just exists to call the activity kicker
        pass

    @activity_kick
    def save_settings(self):

        #Pull out the requisite info, and write it back to config
        self.tank_light_schedule["sunrise_hhmm"] = self.sunrise_selector.get_hhmm()
        self.tank_light_schedule["sunset_hhmm"]  = self.sunset_selector.get_hhmm()
        self.tank_light_schedule['blue_lights_at_night'] = True if self.blue_at_night_var.get() == "True" else False

        self.tank_light_schedule['eclipse_enabled'] = True if self.period_blue_lights_enabled.get() == "True" else False


        blue_period_m = int(self.blue_length_min_var.get())
        white_period_m = int(self.white_length_min_var.get())

        self.tank_light_schedule['eclipse_frequency_min'] = blue_period_m + white_period_m
        self.tank_light_schedule['eclipse_duration_min'] = blue_period_m

        for l_id in self.enable_vars:
            for c_id, c_var in self.enable_vars[l_id].items():
                self.tank_light_schedule['lights'][f"TankLight{l_id}"][c_id] = bool(c_var.get())

        if (self.sunrise_selector.get_hhmm() >= self.sunset_selector.get_hhmm()):
            logger.warning("Bad timing config!")
            ErrorPromptPage("On time must be before Off time!")
        else:
            logger.info("Writing new settings to file...")
            with open(SCHEDULE_CONFIG_FILE, 'w') as jsonfile:
                json.dump(self.config_data, jsonfile, indent=4)

            self.exit()
            RelaunchPromptPage()

class OutletSettingsPage(Subwindow):
    ''' Page for adjusting Outlet Settings '''
    def __init__(self):
        super().__init__("Outlet Settings", draw_exit_button=False)

        #Load the scheduler json file
        this_dir = os.path.dirname(__file__)
        with open(SCHEDULE_CONFIG_FILE, 'r') as jsonfile:
            self.config_data = json.load(jsonfile)

        big_font = ('Arial', 20)
        self.outlet_list = [k for k in self.config_data["outlet_schedules"]]
        self.outlet_inx = 0
        self.title_var = tk.StringVar()
        time_setting_frame = tk.LabelFrame(self.master, text="Outlet", font=fontTuple)
        time_setting_frame.grid(row=1, column =0, sticky='ew', padx=10, pady=10)
        tk.Label(time_setting_frame, textvariable=self.title_var, font=big_font).grid(row=0, column=1)
        tk.Label(time_setting_frame, text="On Time:", font=big_font).grid(row=1, column=0)
        tk.Label(time_setting_frame, text="Off Time:", font=big_font).grid(row=2, column=0)

        self.mode_selector = tk.StringVar()
        OPTIONS = ["off", "on", "timer"]
        self.optionmenu = tk.OptionMenu(time_setting_frame, self.mode_selector, *OPTIONS)
        self.optionmenu.config(font=('Arial', 20)) # set the button font
        menu = time_setting_frame.nametowidget(self.optionmenu.menuname)
        menu.config(font=('Arial', 20))  # Set the dropdown menu's font
        self.optionmenu.grid(row=3, column=1, sticky='w')
        tk.Label(time_setting_frame, text="Mode", font=big_font).grid(row=3, column=0)
        self.mode_selector.trace("w", self.mode_selector_callback)

        self.sunrise_selector = TimeSelector(time_setting_frame, 1200)
        self.sunrise_selector.frame.grid(row=1, column=1)

        self.sunset_selector = TimeSelector(time_setting_frame, 1200)
        self.sunset_selector.frame.grid(row=2, column=1)


        button_frame = tk.Frame(self.master)
        button_frame.grid(row=2, column =0, sticky='ew', padx=10, pady=10)

        btn = tk.Button(button_frame, text="Previous\nOutlet", font=fontTuple, width=10, height=4, bg='#BBBBBB', command=self.back)
        btn.grid(row=2, column=0, padx=10, pady=10)

        btn = tk.Button(button_frame, text="Next\nOutlet", font=fontTuple, width=10, height=4, bg='#BBBBBB', command=self.next, )
        btn.grid(row=2, column=1, padx=10, pady=10)

        btn = tk.Button(self.master, text="Cancel", font=fontTuple, width=10, height=4, bg='#ff5733', command=self.exit)
        btn.grid(row=1, column=1, padx=10, pady=10)
        btn = tk.Button(button_frame, text="Save", font=fontTuple, width=10, height=4, bg='#00ff00', command=self.save_settings)
        btn.grid(row=2, column=2, padx=10, pady=10)


        self.info_text = tk.StringVar()
        tk.Label(self.master, textvariable=self.info_text, font=('Arial', 16)).grid(row=4, column=0)


        tk.Label(self.master, text="Changes will take effect on next GUI relaunch.", font=('Arial', 16)).grid(row=5, column=0)

        self.redraw_for_outlet(self.outlet_list[self.outlet_inx])

    @activity_kick
    def mode_selector_callback(self, *args):
        '''Callback function for when the Mode dropdown changes. If 'Timer' is selected, enable time fields.
        Otherwise, disable. '''
        if (self.mode_selector.get() == 'timer'):
            self.sunrise_selector.enable()
            self.sunset_selector.enable()
        else:
            self.sunset_selector.disable()
            self.sunrise_selector.disable()


    def cache_settings(self):
        ''' Save the settings on the screen currently as you cycle through outlets'''
        outlet_name = self.outlet_list[self.outlet_inx]
        this_sched = self.get_outlet_sched(outlet_name)

        this_sched["mode"] = self.mode_selector.get()
        this_sched["sunrise_hhmm"] = self.sunrise_selector.get_hhmm()
        this_sched["sunset_hhmm"]  = self.sunset_selector.get_hhmm()

    @activity_kick
    def next(self):
        '''Callback function to move to next outlet.
        '''
        self.cache_settings()
        self.outlet_inx+=1
        if (self.outlet_inx >= len(self.outlet_list)):
            self.outlet_inx = 0

        self.redraw_for_outlet(self.outlet_list[self.outlet_inx])

    @activity_kick
    def back(self):
        ''' Callback function to move to previous outlet.'''
        self.cache_settings()
        self.outlet_inx-=1
        if (self.outlet_inx < 0):
            self.outlet_inx = len(self.outlet_list) - 1

        self.redraw_for_outlet(self.outlet_list[self.outlet_inx])


    def redraw_for_outlet(self, outlet_name:str):
        '''Reconfigure the window for the given outlet

        Parameters
        ----------
        outlet_name : str
            Name of outlet to reconfigure window for
        '''
        logger.debug(f'Redrawing for {outlet_name}')
        this_sched = self.get_outlet_sched(outlet_name)

        if (this_sched['description']) != '':
            self.title_var.set(f"{outlet_name.capitalize()} ({this_sched['description']})")
        else:
            self.title_var.set(f"{outlet_name.capitalize()}")

        self.sunrise_selector.set_time(this_sched['sunrise_hhmm'])
        self.sunset_selector.set_time(this_sched['sunset_hhmm'])
        self.mode_selector.set(this_sched['mode']) #This will disable the time fields if on/off selected, or otherwise enable them

    def get_outlet_sched(self, name:str) ->dict:
        ''' Get the schedule for this outlet as a dict'''
        return self.config_data["outlet_schedules"][name]

    @activity_kick
    def save_settings(self):
        '''Save the cached settings to file
        '''
        self.cache_settings()
        #Pull out the requisite info, and write it back to config
        for outlet_name in self.outlet_list:
            this_sched = self.get_outlet_sched(outlet_name)

            if (this_sched["sunrise_hhmm"] >= this_sched["sunset_hhmm"]):
                logger.warning("Bad timing config!")
                ErrorPromptPage("On time must be before Off time!")
                return #This needs to be fixed before doing anything

        #If everything was valid, save to file
        logger.info("Writing new settings to file...")
        with open(SCHEDULE_CONFIG_FILE, 'w') as jsonfile:
            json.dump(self.config_data, jsonfile, indent=4)

        self.exit()
        RelaunchPromptPage()

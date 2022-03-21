'''System Settings GUI Elements    '''

import shutil
from helpers import *
from windows import (Subwindow, fontTuple, ErrorPromptPage)
import sys

class SystemSettingsPage(Subwindow):

    def __init__(self):
        super().__init__("System Settings")

        buttons = [
            {'text':"About",            'callback': lambda: AboutPage()},
            {'text':"Shutdown\nBox",    'callback': shutdown_pi},
            {'text':"Exit GUI",         'callback': self.quitGui},
            {'text':"Network\nSettings", 'callback': lambda: NetworkSettingsPage()},
            {'text':"Set Time",         'callback': lambda: SetSystemTimePage()},
            {'text':"Restore\nDefaults", 'callback': self.restore_defaults}
        ]

        self.drawButtonGrid(buttons)


    def quitGui(self):
        """Close this entire GUI program
        """
        self.master.quit()

    def restore_defaults(self):
        ''' Copy the default config file on top of existing'''
        logger.info("Restoring default schedule")
        shutil.copyfile(SCHEDULE_CONFIG_DEFAULT_FILE, SCHEDULE_CONFIG_FILE)

        self.exit()
        RebootPromptPage()

class SetSystemTimePage(Subwindow):
    def __init__(self):
        super().__init__("System Time Settings", draw_exit_button=False)

        tk.Label(self.master, text="Time (hh:mm)", font=('Arial', 20)).grid(row=1, column=0)
        tk.Label(self.master, text="Date (YYYY-MM-DD)", font=('Arial', 20)).grid(row=3, column=0)

        self.time_select = TimeSelector(self.master, timeToHhmm(datetime.datetime.now().time()))
        self.time_select.grid(row=2, column=0, pady=10, padx=10)

        self.date_select = DateSelector(self.master, datetime.datetime.now().date())
        self.date_select.grid(row=4, column=0, pady=10, padx=10)

        btn = tk.Button(self.master, text="Save", font=fontTuple, width=12, height=4, bg='#00ff00', command=self.save)
        btn.grid(row=5, column=2, padx=10, pady=10)

        self.exit_btn.grid(row=1, column=2, padx=10, pady=10)

        tk.Label(self.master, text="Changing time requires GUI to restart.\nNote time channge may not work\nif system is connected to WiFi!",
        font=('Arial', 16)).grid(row=5, column=0)




    def save(self):
        try:
            new_dt = datetime.datetime.combine(self.date_select.get_date(), self.time_select.get_time())
            set_datetime(new_dt)
            RebootPromptPage(allow_defer=False)

        except ValueError:
            ErrorPromptPage("Invalid date/time!")


class NetworkSettingsPage(Subwindow):
    def __init__(self):
        super().__init__("Network Info")

        tk.Label(self.master, text=f"IP Address:", font=("Arial", 24)).grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self.master, text=f"{get_ip()}", font=("Arial", 24)).grid(row=1, column=1, padx=5, pady= 5)
        tk.Label(self.master, text=f"WiFi status: ", font=('Arial', 24)).grid(row=2, column=0, padx=5, pady=5)
        self.wifi_status_var = tk.StringVar()
        tk.Label(self.master, textvar=self.wifi_status_var, font=("Arial", 24)).grid(row=2, column=1, padx=5, pady=5)

        self.wifi_button_var = tk.StringVar()
        self.update_wifi_button()

        txt= 'To change connected WiFi network\n' + \
             'exit GUI and use WiFi dropdown.'
        tk.Label(self.master, text=txt, font=("Arial", 16)).place(x=50, y=400)


        buttons = [
            {'text': self.wifi_button_var,  'callback': self.toggle_wifi}
             ]
        self.drawButtonGrid(buttons)

    def toggle_wifi(self):
        set_wifi_state(not is_wifi_on())
        self.update_wifi_button()

    def update_wifi_button(self):
        if (is_wifi_on()):
            self.wifi_button_var.set("Turn WiFi\nOff")
            self.wifi_status_var.set("On")
        else:
            self.wifi_button_var.set("Turn WiFi\nOn")
            self.wifi_status_var.set("Off")

class AboutPage(Subwindow):
    def __init__(self):
        super().__init__("About")

        tk.Label(self.master,
        text=f'Version: {get_git_version()}',
        font=('Arial', 20)).pack(side=tk.TOP, pady=100)


        buttons = [
            {'text': "Back home",  'callback': self.destroy_all}
             ]
        self.drawButtonGrid(buttons)


class RebootPromptPage(Subwindow):
    ''' A Page to prompt the user to restart the GUI'''
    def __init__(self, allow_defer=True):
        super().__init__("Relaunch Prompt", draw_exit_button=False)

        buttons = [
            {'text': "Relaunch\nNow",   'callback': lambda: sys.exit(1), 'color':'#ff5733'}
        ]

        if (allow_defer):
            buttons.append({'text': "Relaunch\nLater", 'callback': self.exit})

        self.drawButtonGrid(buttons)


        tk.Label(self.master,
        text="The GUI must restart for changes to take effect!",
        font=('Arial', 20)).pack(side=tk.TOP, pady=75)
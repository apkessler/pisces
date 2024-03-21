"""System Settings GUI Elements    """

import shutil
import tkinter as tk
import datetime
import sys
import time
from loguru import logger

from helpers import (
    get_git_version,
    SCHEDULE_CONFIG_DEFAULT_FILE,
    SCHEDULE_CONFIG_FILE,
    set_datetime,
    DateSelector,
    TimeSelector,
    timeToHhmm,
    shutdown_pi,
    get_ip,
    is_wifi_on,
    set_wifi_state,
    PhWarningHelper,
)
from windows import (
    Subwindow,
    fontTuple,
    ErrorPromptPage,
    ConfirmPromptPage,
    activity_kick,
)


class SystemSettingsPage(Subwindow):
    def __init__(self):
        super().__init__("System Settings")

        buttons = [
            {"text": "About", "callback": lambda: AboutPage()},
            {
                "text": "Shutdown\nBox",
                "callback": lambda: ConfirmPromptPage(
                    "Are you sure you want to shutdown?", shutdown_pi
                ),
            },
            {
                "text": "Exit GUI",
                "callback": lambda: ConfirmPromptPage(
                    "Are you sure you want to quit?", self.quitGui
                ),
            },
            {"text": "Network\nSettings", "callback": lambda: NetworkSettingsPage()},
            {"text": "Set Time", "callback": lambda: SetSystemTimePage()},
            {
                "text": "Restore\nDefaults",
                "callback": lambda: ConfirmPromptPage(
                    "Are you sure?", self.restore_defaults
                ),
            },
        ]

        self.drawButtonGrid(buttons)

    def quitGui(self):
        """Close this entire GUI program"""
        self.master.quit()

    def restore_defaults(self):
        """Copy the default config file on top of existing"""
        logger.info("Restoring default schedule")
        shutil.copyfile(SCHEDULE_CONFIG_DEFAULT_FILE, SCHEDULE_CONFIG_FILE)
        PhWarningHelper().restore_defaults()
        self.exit()
        RelaunchPromptPage(allow_defer=False)


class SetSystemTimePage(Subwindow):
    def __init__(self):
        # We manually draw the exit button a grid below...
        super().__init__("System Time Settings", draw_exit_button=False)

        tk.Label(self.master, text="Time (hh:mm)", font=("Arial", 20)).grid(
            row=1, column=0
        )
        tk.Label(self.master, text="Date (YYYY-MM-DD)", font=("Arial", 20)).grid(
            row=3, column=0
        )

        self.time_select = TimeSelector(
            self.master, timeToHhmm(datetime.datetime.now().time())
        )
        self.time_select.grid(row=2, column=0, pady=10, padx=10)

        self.date_select = DateSelector(self.master, datetime.datetime.now().date())
        self.date_select.grid(row=4, column=0, pady=10, padx=10)

        btn = tk.Button(
            self.master,
            text="Save and\nRelaunch",
            font=fontTuple,
            width=12,
            height=4,
            bg="#00ff00",
            command=self.save_callback,
        )
        btn.grid(row=5, column=2, padx=10, pady=10)

        self.exit_btn.grid(row=1, column=2, padx=10, pady=10)

        tk.Label(
            self.master,
            text="System will automatically update\nto internet time if available.",
            font=("Arial", 16),
        ).grid(row=5, column=0)
        tk.Label(
            self.master,
            text="Changing time will cause GUI to restart.",
            font=("Arial", 16),
        ).grid(row=6, column=0)

    @activity_kick
    def save_callback(self):
        """Function called when "Save" button hit.
        Grabs date/time from user input, and calls system set-time interface.
        """
        try:
            new_dt = datetime.datetime.combine(
                self.date_select.get_date(), self.time_select.get_time()
            )
            err = set_datetime(new_dt)
            logger.debug(f"Set time error: {err}")

            # Rather then call RelaunchPromptPage here, we just go straight to exit/relaunch.
            # This is because changing the time can have unexpected behavior wrt tkinter event
            # expirations, etc. So for example system might suddenly lock, blocking you from restarting.
            time.sleep(0.5)  # Delay for 0.5sec to allow logs to flush
            sys.exit(1)

        except ValueError:
            ErrorPromptPage("Invalid date/time!")


class NetworkSettingsPage(Subwindow):
    def __init__(self):
        super().__init__("Network Info", draw_wifi_indicator=True)

        f = tk.Frame(self.master)
        f.place(x=50, y=80)
        tk.Label(f, text="IP Address:", font=("Arial", 24)).grid(
            row=1, column=0, padx=5, pady=2
        )
        self.ip_addr_var = tk.StringVar()
        tk.Label(f, textvar=self.ip_addr_var, font=("Arial", 24)).grid(
            row=1, column=1, padx=5, pady=2
        )

        tk.Label(f, text="WiFi status: ", font=("Arial", 24)).grid(
            row=2, column=0, padx=5, pady=2
        )
        self.wifi_status_var = tk.StringVar()
        tk.Label(f, textvar=self.wifi_status_var, font=("Arial", 24)).grid(
            row=2, column=1, padx=5, pady=2
        )

        self.wifi_button_var = tk.StringVar()
        self.update_wifi_button()

        txt = "If internet time is very different than system time, GUI may restart."
        tk.Label(self.master, text=txt, font=("Arial", 15)).place(x=20, y=390)

        txt = "To change WiFi network, exit GUI and use WiFi dropdown."
        tk.Label(self.master, text=txt, font=("Arial", 15)).place(x=20, y=425)

        buttons = [{"text": self.wifi_button_var, "callback": self.toggle_wifi}]
        self.drawButtonGrid(buttons)

        self.refresh_data()

    def refresh_data(self):
        logger.debug("Refreshing IP data")
        self.ip_addr_var.set(get_ip())
        self.master.after(2000, self.refresh_data)

    @activity_kick
    def toggle_wifi(self):
        """Callback when Toggle WiFi button hit"""
        set_wifi_state(not is_wifi_on())
        self.update_wifi_button()

    def update_wifi_button(self):
        """Check current state of Wifi and update text/icons"""
        self.update_wifi_indicator()

        if is_wifi_on():
            self.wifi_button_var.set("Turn WiFi\nOff")
            self.wifi_status_var.set("On")
        else:
            self.wifi_button_var.set("Turn WiFi\nOn")
            self.wifi_status_var.set("Off")

    def exit(self):
        """On exit from this window, force WiFi indicator on main screen to update"""
        logger.info("Updating Wifi status on MainWindow")
        self.main_window.update_wifi_indicator()
        super().exit()


class AboutPage(Subwindow):
    def __init__(self):
        super().__init__("About")

        tk.Label(
            self.master, text=f"Version: {get_git_version()}", font=("Arial", 20)
        ).pack(side=tk.TOP, pady=100)

        buttons = [{"text": "Back home", "callback": self.destroy_all}]
        self.drawButtonGrid(buttons)


class RelaunchPromptPage(Subwindow):
    """A Page to prompt the user to restart the GUI
    Note that timed reboot might now work correctly after adjusting system time.
    """

    def __init__(self, allow_defer=True, auto_accept_time_sec=10):
        super().__init__(
            "Relaunch Prompt", draw_lock_button=False, draw_exit_button=False
        )
        self.auto_accept_time_sec = auto_accept_time_sec
        buttons = [
            {
                "text": "Relaunch\nNow",
                "callback": self.do_the_relaunch,
                "color": "#ff5733",
            }
        ]

        self.kick_activity_watchdog(source="RelaunchPromptInit")
        self.init_time_monotonic_sec = time.monotonic()
        tk.Label(
            self.master,
            text="The GUI must restart for changes to take effect!",
            font=("Arial", 20),
        ).pack(side=tk.TOP, pady=50)

        if allow_defer:
            buttons.append({"text": "Relaunch\nLater", "callback": self.exit})
        else:
            tk.Label(
                self.master,
                text=f"The GUI will restart automatically in {auto_accept_time_sec}sec.",
                font=("Arial", 20),
            ).pack(side=tk.TOP, pady=10)
            logger.debug(self.master)
            self.master.after(1000, self.check_time)

        self.drawButtonGrid(buttons)

    @activity_kick
    def check_time(self):
        """We use a monotonic clock to look at the reboot countdown, since this might happen
        right after a system time change and things may get weird relying on just `after`
        (but even, weird stuff might happen, so not reccomended right after changing system time.)
        """

        mono_now = time.monotonic()
        elp_sec = mono_now - self.init_time_monotonic_sec
        logger.debug(f"Monotonic delta={elp_sec:.2f}sec")
        if elp_sec >= self.auto_accept_time_sec:
            self.do_the_relaunch()
        else:
            self.master.after(1000, self.check_time)

    def do_the_relaunch(self):
        logger.warning("Doing the relaunch!")
        time.sleep(0.5)  # Give logs time to flush, etc.
        sys.exit(1)  # Exit with error so systemd relaunches the service

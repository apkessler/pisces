import datetime
import socket
import subprocess
import tkinter as tk
import json
import os
from typing import Tuple
import calendar
import shlex
from loguru import logger
from typing import Optional
from windows import fontTuple, activity_kick
import textwrap
import shutil

SCHEDULE_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "../data/schedule.json")
SCHEDULE_CONFIG_DEFAULT_FILE = os.path.join(
    os.path.dirname(__file__), "schedule.default.json"
)
ICON_PATH = os.path.join(os.path.dirname(__file__), "icons")


try:
    import systemd.daemon

    has_systemd = True
except ModuleNotFoundError:
    print("Cannot find systemd module")
    has_systemd = False


def notify_systemd_watchdog():
    """Send systemd the watchdog kick notification."""

    # logger.debug('systemd watchdog kick')
    if has_systemd:
        systemd.daemon.notify("WATCHDOG=1")
    else:
        pass


def ph_to_color(ph: float) -> str:
    """Convert a pH value to color based on API Freshwater test kit color map

    Parameters
    ----------
    ph : float
        pH to convert

    Returns
    -------
    str
        Closest Hex RGB color code

    """
    color_map = [
        [6.0, "#FCF090"],
        [6.4, "#F4F3BC"],
        [6.6, "#CADDA7"],
        [6.8, "#B3D2B7"],
        [7.0, "#98C6B2"],
        [7.2, "#82BBB7"],
        [7.4, "#C9A443"],
        [7.8, "#DE9D57"],
        [8.0, "#BF815B"],
        [8.2, "#985854"],
        [8.4, "#714275"],
        [8.8, "#52366D"],
    ]

    best_score = 100
    best_item = None
    for item in color_map:
        score = abs(item[0] - ph)
        if score < best_score:
            best_score = score
            best_item = item

    return best_item[1]


class PhCalibrationHelper:
    PH_CALIBRATION_PATH = os.path.join(
        os.path.dirname(__file__), "../data/ph_calibrations.json"
    )

    def get_latest_ph_calibration_date(self) -> Optional[datetime.datetime]:
        """Get the datetime of the latest calibration, if any"""
        ts_list = self.get_ph_calibrations()
        if len(ts_list) == 0:
            return None

        return max(ts_list)

    def get_ph_calibrations(self) -> list[datetime.datetime]:
        """Get the history of ph calibrations"""

        try:
            with open(self.PH_CALIBRATION_PATH) as fp:
                caldata = json.load(fp)
        except FileNotFoundError:
            logger.warning(
                f"No PH calibration data exists in {self.PH_CALIBRATION_PATH}!"
            )
            return []

        return [
            datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
            for ts_str in caldata.keys()
        ]

    def record_calibration(self, dt: datetime.datetime, data: dict):
        """Make a record of a calibration"""

        # Calibraton file is a json, where each key/value pair is "YYYY-MM-DDThh:mm:ss":dict
        # right now dicts are empty
        ts = dt.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            logger.debug("cal file exists")
            with open(self.PH_CALIBRATION_PATH, "r") as fp:
                caldata = json.load(fp)
        except FileNotFoundError:
            logger.debug("cal file does NOT exist")
            caldata = {}

        caldata[ts] = data

        with open(self.PH_CALIBRATION_PATH, "w") as fp:
            json.dump(caldata, fp)

        logger.info(f"Saved a calibration {ts=}")


class PhMessages:
    MSG_PH_OUTSIDE_OF_RANGE = "pH outside of expected range! Calibration may be needed."
    MSG_PH_SIX_MONTHS_OLD = (
        "Last pH calibration >6mo ago. pH readings may be inaccurate."
    )
    MSG_PH_ONE_YEAR_OLD = "Last pH calibration >1yr ago. Calibration required."
    MSG_PH_CAL_NOT_FOUND = "No pH calibration found! Calibration required."
    MSG_RECALIBRATION_REQUIRED = "Calibration required!"
    MSG_RECALIBRATION_MAYBE_NEEDED = "Calibration may be needed!"


class PhWarningHelper:
    PHWARNINGS_CONFIG_FILE = os.path.join(
        os.path.dirname(__file__), "../data/ph_warnings.json"
    )
    PHWARNINGS_CONFIG_DEFAULT_FILE = os.path.join(
        os.path.dirname(__file__), "ph_warnings.default.json"
    )

    def __init__(self):
        if not os.path.exists(self.PHWARNINGS_CONFIG_FILE):
            # Copy the default config file!
            logger.info("No PhWarnings json file found - copying default file.")
            shutil.copyfile(
                self.PHWARNINGS_CONFIG_DEFAULT_FILE, self.PHWARNINGS_CONFIG_FILE
            )

        with open(self.PHWARNINGS_CONFIG_FILE, "r") as configfile:
            self.jData = json.load(configfile)

    def get_ph_warning_message(
        self,
        ph_now: float,
        last_cal_date: Optional[datetime.datetime],
        time_now=datetime.datetime,
    ) -> tuple[str, str]:
        if last_cal_date is None:
            return (
                PhMessages.MSG_RECALIBRATION_REQUIRED,
                PhMessages.MSG_PH_CAL_NOT_FOUND,
            )

        dt_delta = time_now - last_cal_date  # See how much time has passed

        if dt_delta.days >= 365:
            return PhMessages.MSG_RECALIBRATION_REQUIRED, PhMessages.MSG_PH_ONE_YEAR_OLD

        if dt_delta.days >= 180:
            return (
                PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED,
                PhMessages.MSG_PH_SIX_MONTHS_OLD,
            )

        # We're ok with the date range. Now, check the ph
        if ph_now < self.get_lower_bound() or ph_now > self.get_upper_bound():
            return (
                PhMessages.MSG_RECALIBRATION_MAYBE_NEEDED,
                PhMessages.MSG_PH_OUTSIDE_OF_RANGE,
            )

        return "", ""

    def get_lower_bound(self) -> float:
        return self.jData["lower_bound"]

    def get_upper_bound(self) -> float:
        return self.jData["upper_bound"]

    def save_new_settings(self, lower_bound: float, upper_bound: float):
        if lower_bound >= upper_bound:
            raise ValueError("Lower bound must be < upper bound")

        self.jData["lower_bound"] = lower_bound
        self.jData["upper_bound"] = upper_bound

        with open(self.PHWARNINGS_CONFIG_FILE, "w") as configfile:
            json.dump(self.jData, configfile, indent=4)

        logger.info(
            f"Wrote new pH warning limits to file ({lower_bound},{upper_bound})"
        )


def timeToHhmm(time: datetime.time) -> int:
    """Convert a datetime._time object to a simple time integer in form hhmm

    Parameters
    ----------
    time : dt._time
        Time to convert

    Returns
    -------
    int
        Equivalent hhmm int
    """
    return (time.hour * 100) + time.minute


def get_ip() -> str:
    """
    Get IP address of this device, return as string.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def sys_call(cmd: str) -> str:
    output = ""
    try:
        tokens = shlex.split(
            cmd
        )  # Use shlex.split so quoted spaces are treated as a single token
        logger.debug(tokens)
        process = subprocess.Popen(tokens, stdout=subprocess.PIPE)
        output = process.communicate()[0]
    except FileNotFoundError:
        logger.error(f"Could not execute sys call: '{cmd}'")
        output = None
    finally:
        return output


def set_datetime(the_datetime: datetime.datetime):
    """Set the system date time to provided value.
    Return success/fail
    """
    # Turn NTP off so we can change the time
    sys_call("/usr/bin/sudo /usr/bin/timedatectl set-ntp 0")

    time = the_datetime.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Setting time to {time}")
    sys_call(f'/usr/bin/sudo /usr/bin/timedatectl set-time "{time}"')

    # Turn NTP back on (note this may override the change we just tried to make)
    sys_call("/usr/bin/sudo /usr/bin/timedatectl set-ntp 1")

    # Look at what the time is now
    new_now = datetime.datetime.now()
    time_error = new_now - the_datetime
    logger.debug(f"Err={time_error}")
    return time_error.total_seconds() > 1.5


def reboot_pi():
    logger.info("restarting the Pi")
    sys_call("/usr/bin/sudo /sbin/shutdown -r now")


# modular function to shutdown Pi
def shutdown_pi():
    logger.info("shutting down the Pi")
    sys_call("/usr/bin/sudo /sbin/shutdown -h now")


def get_git_version() -> str:
    """Get the git latest git hash. Only works if code is actually cloned

    Returns
    -------
    str
        Latest git hash
    """
    return (
        subprocess.check_output(
            ["git", "describe", "--always"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        .strip()
        .decode()
    )


def is_wifi_on() -> bool:
    """Get WiFi radio status via `rfkill`.

    Returns
    -------
    bool
        True if WiFi is on, False if Wifi is off or unable to determine
    """
    resp = sys_call("rfkill -J")
    try:
        jData = json.loads(resp)
        for interface in jData[""]:
            if interface["type"] == "wlan":
                return (
                    interface["soft"] == "unblocked"
                    and interface["hard"] == "unblocked"
                )
    except TypeError:
        logger.error("Could not get wlan radio status")
    return False


def set_wifi_state(state: bool) -> bool:
    """Set WiFi radio is given state (on/off)

    Parameters
    ----------
    state : bool
        State to set radio. True = On, False = Off

    Returns
    -------
    bool
        True if successful
    """
    cmd = "unblock" if state else "block"
    return sys_call(f"sudo rfkill {cmd} wlan") is not None


def set_local_ap_mode(mode: bool) -> bool:
    logger.info(f"Setting local AP mode to {mode}")


def get_start_of_year(dt: datetime.datetime) -> datetime.datetime:
    return datetime.datetime(dt.year, 1, 1)


def get_end_of_year(dt: datetime.datetime) -> datetime.datetime:
    return datetime.datetime(dt.year, 12, 31, 23, 59)


def get_start_of_month(dt: datetime.datetime) -> datetime.datetime:
    return datetime.datetime(dt.year, dt.month, 1)


def get_end_of_month(dt: datetime.datetime) -> datetime.datetime:
    days_in_month = calendar.monthrange(dt.year, dt.month)[1]
    return datetime.datetime(dt.year, dt.month, days_in_month, 23, 59)


class DateSelector:
    """Helper Class for drawing date selector GUI elements"""

    def __init__(self, master, default_date: datetime.date):
        # self.style = ttk.Style()
        # self.style.theme_use("clam")
        # self.style.configure("TSpinbox", arrowsize=30, arrowcolor="green")

        self.frame = tk.Frame(master)
        self.year = tk.StringVar()
        self.month = tk.StringVar()
        self.day = tk.StringVar()

        self.year.set(default_date.year)
        self.month.set(default_date.month)
        self.day.set(default_date.day)

        s = tk.Spinbox(
            self.frame,
            from_=2022,
            to=2100,
            wrap=True,
            textvariable=self.year,
            width=4,
            font=("Courier", 30),
            justify=tk.CENTER,
            command=self.spinbox_update,
        )
        s.pack(side=tk.LEFT)

        s = tk.Spinbox(
            self.frame,
            from_=1,
            to=12,
            wrap=True,
            textvariable=self.month,
            width=4,
            font=("Courier", 30),
            justify=tk.CENTER,
            command=self.spinbox_update,
        )
        s.pack(side=tk.LEFT)

        s = tk.Spinbox(
            self.frame,
            from_=1,
            to=31,
            wrap=True,
            textvariable=self.day,
            width=4,
            font=("Courier", 30),
            justify=tk.CENTER,
            command=self.spinbox_update,
        )
        s.pack(side=tk.LEFT)

    @activity_kick
    def spinbox_update(self):
        pass

    def get_date(self) -> datetime.date:
        return datetime.datetime(
            year=int(self.year.get()),
            month=int(self.month.get()),
            day=int(self.day.get()),
        ).date()

    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)


class TimeSelector:
    """Helper Class for drawing time selector GUI elements"""

    def __init__(self, master, default_hhmm: int):
        # self.style = ttk.Style()
        # self.style.theme_use("clam")
        # self.style.configure("TSpinbox", arrowsize=30, arrowcolor="green")

        self.frame = tk.Frame(master)
        self.hh_var = tk.StringVar()
        hh, mm = self.split_hhmm(default_hhmm)
        self.hh_var.set(str(hh))
        self.hh_select = tk.Spinbox(
            self.frame,
            from_=0,
            to=23,
            wrap=True,
            textvariable=self.hh_var,
            width=4,
            font=("Courier", 30),
            #                        style='TSpinbox',
            justify=tk.CENTER,
            command=self.spinbox_update,
        )

        self.mm_var = tk.StringVar()
        self.mm_var.set(str(mm))
        self.mm_select = tk.Spinbox(
            self.frame,
            from_=0,
            to=59,
            wrap=True,
            textvariable=self.mm_var,
            width=4,
            font=("Courier", 30),
            justify=tk.CENTER,
            command=self.spinbox_update,
        )

        self.hh_select.pack(side=tk.LEFT)
        tk.Label(self.frame, text=":", font=fontTuple).pack(side=tk.LEFT)
        self.mm_select.pack(side=tk.LEFT)

    @activity_kick
    def spinbox_update(self):
        pass

    def get_hhmm(self) -> int:
        hh_str = self.hh_var.get()
        mm_str = self.mm_var.get()
        return int(hh_str) * 100 + int(mm_str)

    def get_time(self) -> datetime.time:
        return datetime.time(hour=int(self.hh_var.get()), minute=int(self.mm_var.get()))

    def set_time(self, hhmm: int):
        hh, mm = self.split_hhmm(hhmm)
        self.hh_var.set(hh)
        self.mm_var.set(mm)

    def enable(self):
        self.hh_select.config(state=tk.NORMAL)
        self.mm_select.config(state=tk.NORMAL)

    def disable(self):
        self.hh_select.config(state=tk.DISABLED)
        self.mm_select.config(state=tk.DISABLED)

    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)

    @staticmethod
    def split_hhmm(hhmm: int) -> Tuple[int, int]:
        hh = int(hhmm / 100)
        mm = hhmm - hh * 100
        return hh, mm


def wrap_text(text: str, width: int) -> str:
    """Wrap a string to fixed width and return single
    string new line.
    """
    return "\n".join(textwrap.wrap(text, width))


if __name__ == "__main__":
    ph_to_color(1.0)
    ph_to_color(7.0)

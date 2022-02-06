
import datetime
import socket
import subprocess
import tkinter as tk
from typing import Tuple
from windows import fontTuple
from loguru import logger

def timeToHhmm(time:datetime.time) -> int:
    ''' Convert a datetime._time object to a simple time integer in form hhmm

    Parameters
    ----------
    time : dt._time
        Time to convert

    Returns
    -------
    int
        Equivalent hhmm int
    '''
    return (time.hour * 100) + time.minute

def get_ip() -> str:
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

def sys_call(cmd:str) -> str:
    output = ""
    try:
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
    except FileNotFoundError:
        output = f"Could not execute sys call: '{cmd}'"
    finally:
        logger.info(output)

def set_datetime(the_datetime:datetime.datetime):
    #sudo date -s YYYY-MM-DD HH:MM:SS
    #date_time = now.strftime("%m/%d/%Y, %H:%M:%S")

    time = the_datetime.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Setting time to {time}")
    sys_call(f'/usr/bin/sudo /usr/bin/date -s {time}')

def reboot_pi():
    logger.info("restarting the Pi")
    sys_call("/usr/bin/sudo /sbin/shutdown -r now")

# modular function to shutdown Pi
def shutdown_pi():
    logger.info("shutting down the Pi")
    sys_call("/usr/bin/sudo /sbin/shutdown -h now")

# modular function to shutdown Pi
def get_git_version():
    sys_call("cd /home/pi/Repositories/pisces/; git describe")


class DateSelector():
    ''' Helper Class for drawing date selector GUI elements'''
    def __init__(self, master, default_date:datetime.date):

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
                        font=('Courier', 30),
                        justify=tk.CENTER
        )
        s.pack(side=tk.LEFT)

        s = tk.Spinbox(
                        self.frame,
                        from_=1,
                        to=12,
                        wrap=True,
                        textvariable=self.month,
                        width=4,
                        font=('Courier', 30),
                        justify=tk.CENTER
        )
        s.pack(side=tk.LEFT)



        s = tk.Spinbox(
                        self.frame,
                        from_=1,
                        to=31,
                        wrap=True,
                        textvariable=self.day,
                        width=4,
                        font=('Courier', 30),
                        justify=tk.CENTER
        )
        s.pack(side=tk.LEFT)

    def get_date(self) -> datetime.date:
        return datetime.datetime(
            year=int(self.year.get()),
            month=int(self.month.get()),
            day=int(self.day.get())
            ).date()


class TimeSelector():
    ''' Helper Class for drawing time selector GUI elements'''
    def __init__(self, master, default_hhmm:int):

        # self.style = ttk.Style()
        # self.style.theme_use("clam")
        # self.style.configure("TSpinbox", arrowsize=30, arrowcolor="green")

        self.frame = tk.Frame(master)
        self.hh_var = tk.StringVar()
        hh,mm = self.split_hhmm(default_hhmm)
        self.hh_var.set(str(hh))
        hh_select = tk.Spinbox(
                        self.frame,
                        from_=0,
                        to=23,
                        wrap=True,
                        textvariable=self.hh_var,
                        width=4,
                        font=('Courier', 30),
#                        style='TSpinbox',
                        justify=tk.CENTER
        )

        self.mm_var = tk.StringVar()
        self.mm_var.set(str(mm))
        mm_select = tk.Spinbox(
                        self.frame,
                        from_=0,
                        to=59,
                        wrap=True,
                        textvariable=self.mm_var,
                        width=4,
                        font=('Courier', 30),
                        justify=tk.CENTER
        )


        hh_select.pack(side=tk.LEFT)
        tk.Label(self.frame, text=":", font=fontTuple).pack(side=tk.LEFT)
        mm_select.pack(side=tk.LEFT)

    def get_hhmm(self) -> int:
        hh_str = self.hh_var.get()
        mm_str = self.mm_var.get()
        return (int(hh_str)*100 + int(mm_str))

    def get_time(self) -> datetime.time:
        return datetime.time(hour=int(self.hh_var.get()), minute=int(self.mm_var.get()))

    @staticmethod
    def split_hhmm(hhmm:int) -> Tuple[int, int]:
        hh = int(hhmm/100)
        mm = hhmm - hh*100
        return hh,mm

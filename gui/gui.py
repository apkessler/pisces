#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Main executable for Pisces GUI.

"""

### Imports

import tkinter as tk
import socket
from typing import NewType


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

### TKinter Stuff

class Subwindow(object):

    def __init__(self, title):
        self.master = tk.Toplevel()
        self.master.wm_geometry("320x240")
        self.master.title(title)
        self.master.grab_set()

        btn = tk.Button(self.master, text="EXIT", command=self.exit)
        btn.pack()

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



class phPage(Subwindow):

    def __init__(self):
        super().__init__("pH Info")



class MainView(object):


    def turnLightsOn(self):
        pass

    def turnLightsOff(self):
        pass

    def resumeSchedule(self):
        pass

    def openTempInfo(self):
        s = TemperaturePage()

    def openPhInfo(self):
        s = phPage()

    def openSettings(self):
        s = SettingsPage()

    def func(self):
        self.count +=1
        print(f"Button hit {self.count} times", flush=True)
        self.tempText.set(f"Temperature\n{self.count:0.2f}°F")
        self.phText.set(f"pH\n{self.count:0.2f}")


    def __init__(self, master):

        self.master = master
        self.count = 0

        self.tempText = tk.StringVar()
        self.tempText.set(f"Temperature\n{self.count:0.2f}°F")

        self.phText = tk.StringVar()
        self.phText.set(f"pH\n{self.count:0.2f}")


        frame = tk.Frame(master)
        frame.place(in_=master, anchor='c', relx=0.5, rely=0.5)



        buttons = [
            ["All Lights\n On", self.turnLightsOn],
            ["All Lights\n Off", self.turnLightsOff],
            ["Resume\nSchedule", self.resumeSchedule],
            [self.tempText, self.openTempInfo],
            [self.phText, self.openPhInfo],
            ["Settings", self.openSettings]
        ]


        for inx, bInfo in  enumerate(buttons):
            f = tk.Frame(frame, width=90, height=90, padx=5, pady=5) #make a frame where button goes
            if (type(bInfo[0]) is str):
                b = tk.Button(f, text=bInfo[0], command=bInfo[1])
            else:
                b = tk.Button(f, textvariable=bInfo[0], command=bInfo[1])



            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight = 1)
            f.grid_propagate(0)

            f.grid(row = int(inx/3), column=inx%3)
            b.grid(sticky="NWSE")



if __name__ == "__main__":
    root = tk.Tk()
    main = MainView(root)
    root.wm_geometry("320x240")
    #root.attributes('-fullscreen', True) #Uncomment to make fullscreen

    root.mainloop()

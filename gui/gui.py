#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Main executable for Pisces GUI.

"""

### Imports

import tkinter as tk
import socket

import datetime

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

class Window(object):
    """Generic window object. Do not instantiate directly.

    Parameters
    ----------
    object : [type]
        [description]
    """

    def __init__(self, title, handle):
        self.master = handle
        self.master.wm_geometry("320x240")
        self.master.title(title)


    def dummy(self):
        pass

    def drawButtonGrid(self, buttonMap):
        """Build the standard grid of buttons

        Parameters
        ----------
        buttonMap : [type]
            [description]
        """
        frame = tk.Frame(self.master)
        frame.place(in_=self.master, anchor='c', relx=0.5, rely=0.5)
        for inx, bInfo in enumerate(buttonMap):
            f = tk.Frame(frame, width=100, height=100, padx=5, pady=5) #make a frame where button goes
            if (type(bInfo[0]) is str):
                b = tk.Button(f, text=bInfo[0], command=bInfo[1])
            else:
                b = tk.Button(f, textvariable=bInfo[0], command=bInfo[1])

            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight = 1)
            f.grid_propagate(0)

            f.grid(row = int(inx/3), column=inx%3)
            b.grid(sticky="NWSE")



class MainWindow(Window):
    """The main window (shown on launch). Should only be one of these.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    def __init__(self, root):
        super().__init__("Main Window", root)
        self.count = 0

        self.tempText = tk.StringVar()
        self.tempText.set(f"Temperature\n{self.count:0.2f}°F")

        self.phText = tk.StringVar()
        self.phText.set(f"pH\n{self.count:0.2f}")


        buttons = [
            ["Toggle Lights\nDay/Night/Off/\nSchedule", self.dummy],
            [self.tempText, lambda: TemperaturePage()],
            [self.phText, lambda: PhPage()],
            ["Fertilizer\nInfo", lambda: ManualFertilizerPage()],
            ["Settings", lambda: SettingsPage()]
        ]

        self.drawButtonGrid(buttons)

        #After we're done setting everything up...
        self.refresh_data()

    def refresh_data(self):
        now = datetime.datetime.now()
        print(f"refreshing at {now}", flush=True)

        #Update all things that need updating

        #todo: update temp
        #todo: update pH

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

    def __init__(self, title):
        super().__init__(title, tk.Toplevel())

        self.master.grab_set()

        btn = tk.Button(self.master, text="Back", width=7, height=1, bg='#ff5733', command=self.exit)
        btn.place(x=250, y=5)


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

        frame = tk.Frame(self.master)
        frame.place(in_=self.master, anchor='c', relx=0.5, rely=0.5)

        buttons = [
            ["Reboot", self.dummy],
            ["Aquarium\nLights", self.dummy],
            ["Grow Lights", self.dummy],
            ["Fertilizer", self.dummy],
            ["Calibrate pH", self.dummy],
            ["System Settings", lambda: SystemSettingsPage()]
        ]


        for inx, bInfo in enumerate(buttons):
            f = tk.Frame(frame, width=100, height=100, padx=5, pady=5) #make a frame where button goes
            if (type(bInfo[0]) is str):
                b = tk.Button(f, text=bInfo[0], command=bInfo[1])
            else:
                b = tk.Button(f, textvariable=bInfo[0], command=bInfo[1])

            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight = 1)
            f.grid_propagate(0)

            f.grid(row = int(inx/3), column=inx%3)
            b.grid(sticky="NWSE")



class SystemSettingsPage(Subwindow):

    def __init__(self):
        super().__init__("System Settings")

        tk.Label(self.master, text=f"IP Address: {get_ip()}", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady= 5)
        tk.Label(self.master, text=f"", font=("Arial", 10)).grid(row=2, column=0)
        tk.Label(self.master, text=f"", font=("Arial", 10)).grid(row=3, column=0)
        frame = tk.Frame(self.master)
        frame.place(in_=self.master, anchor='c', relx=0.5, rely=0.5)

        buttons = [
            ["About", self.dummy],
            ["Shutdown", self.dummy],
            ["Exit GUI", self.quitGui],
            ["Network Info", self.dummy],
            ["Set Time", self.dummy],
            ["Restore\nDefaults", self.dummy]
        ]


        for inx, bInfo in enumerate(buttons):
            f = tk.Frame(frame, width=100, height=100, padx=5, pady=5) #make a frame where button goes
            if (type(bInfo[0]) is str):
                b = tk.Button(f, text=bInfo[0], command=bInfo[1])
            else:
                b = tk.Button(f, textvariable=bInfo[0], command=bInfo[1])

            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight = 1)
            f.grid_propagate(0)

            f.grid(row = int(inx/3), column=inx%3)
            b.grid(sticky="NWSE")


    def quitGui(self):
        """Close this entire GUI program
        """
        self.master.quit()


class PhPage(Subwindow):

    def __init__(self):
        super().__init__("pH Info")


class ManualFertilizerPage(Subwindow):

    def __init__(self):
        super().__init__("Fertilizer Info")

        l = tk.Label(self.master, text="Volume: 3mL", font=("Arial", 10)).grid(row=0, column=0)
        #TODO: text for this button should auto pull from config file
        btn = tk.Button(self.master, text="Dispense\n3mL", width=10, height = 4, command=self.dispenseNormal)
        btn.grid(row=2, column=0, padx=5, pady=2)
        #this is a large dispense to prime the line
        btn = tk.Button(self.master, text="Dispense\n10mL", width=10, height = 4, command=self.dispense10mL)
        btn.grid(row=2, column=1, padx=5, pady=2)

        #this is a large dispense to prime the line
        btn = tk.Button(self.master, text="Prime\n(start)", width=10, height = 4, command=self.primeToggle)
        btn.grid(row=3, column=0, padx=5, pady=2)

        #this is a large dispense to prime the line
        btn = tk.Button(self.master, text="Timer\nSettings", width=10, height = 4, command=lambda: SettingsPage())
        btn.grid(row=3, column=1, padx=5, pady=2)

        #l = tk.Label(self.master, text="3mL").grid(row=0, column=1)

    def dispenseNormal(self):
        pass

    def dispense10mL(self):
        pass

    def primeToggle(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    main = MainWindow(root)
    #root.attributes('-fullscreen', True) #Uncomment to make fullscreen

    root.mainloop()

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

        btn = tk.Button(self.master, text="Back", width=7, height=2, bg='#ff5733', command=self.exit)
        btn.place(x=250, y=10)

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

        tk.Label(self.master, text=f"IP Address: {get_ip()}", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady= 5)
        tk.Label(self.master, text=f"", font=("Arial", 10)).grid(row=2, column=0)
        tk.Label(self.master, text=f"", font=("Arial", 10)).grid(row=3, column=0)


        btn = tk.Button(self.master, text="Quit GUI", width=20, height = 2, command=self.quitGui)
        btn.grid(row=4, column=0, padx=5, pady= 2)

        btn = tk.Button(self.master, text="Reboot", width=20, height = 2, command=self.reboot)
        btn.grid(row=5, column=0, padx=5, pady= 2)

        btn = tk.Button(self.master, text="Shutdown", width=20, height = 2, command=self.shutdown)
        btn.grid(row=6, column=0, padx=5, pady= 2)

    def quitGui(self):
        """Close this entire GUI program
        """
        self.master.quit()

    def reboot(self):
        """Reboot the Raspberry Pi"""
        print("(not) Rebooting!", flush=True)
        pass

    def shutdown(self):
        """Shutdown the Raspberry Pi"""
        print("(not) Shutting down!", flush=True)



class phPage(Subwindow):

    def __init__(self):
        super().__init__("pH Info")


class fertilizerPage(Subwindow):

    def __init__(self):
        super().__init__("Fertilizer Info")

        l = tk.Label(self.master, text="Volume: 3mL", font=("Arial", 10)).grid(row=0, column=0)
        #TODO: text for this button should auto pull from config file
        btn = tk.Button(self.master, text="Dispense\n3mL", width=10, height = 4, command=self.dispenseNormal)
        btn.grid(row=2, column=0, padx=5, pady=2)
        #this is a large dispense to prime the line
        btn = tk.Button(self.master, text="Dispense\n10mL", width=10, height = 4, command=self.dispense10mL)
        btn.grid(row=2, column=1, padx=5, pady=2)

        #l = tk.Label(self.master, text="3mL").grid(row=0, column=1)

    def dispenseNormal(self):
        pass

    def dispense10mL(self):
        pass


class MainView(object):


    def toggleLights(self):
        pass

    def resumeSchedule(self):
        pass

    def openTempInfo(self):
        s = TemperaturePage()

    def openPhInfo(self):
        s = phPage()

    def fertilizerInfo(self):
        s = fertilizerPage()

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
            ["Toggle Lights\nDay/Night/Off", self.toggleLights],
            ["Resume\nSchedule", self.resumeSchedule],
            [self.tempText, self.openTempInfo],
            [self.phText, self.openPhInfo],
            ["Fertilizer\nInfo", self.fertilizerInfo],
            ["Settings", self.openSettings]
        ]


        for inx, bInfo in  enumerate(buttons):
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



if __name__ == "__main__":
    root = tk.Tk()
    main = MainView(root)
    root.wm_geometry("320x240")
    #root.attributes('-fullscreen', True) #Uncomment to make fullscreen

    root.mainloop()

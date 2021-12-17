#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Main executable for Pisces GUI.

"""

### Imports

import tkinter as tk
import socket
import logging
import datetime
import hardwareControl_pb2
import hardwareControl_pb2_grpc
from hardwareControl_client import HardwareControlClient
import grpc
from run_stepper import dispense
import threading

ADDRESS = "localhost"
PORT = "50051"


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

hwCntrl = None #Global stub, because its easiest

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
        self.buttons = []
        frame = tk.Frame(self.master)
        frame.place(in_=self.master, anchor='c', relx=0.5, rely=0.55)
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
            self.buttons.append(b)



class MainWindow(Window):
    """The main window (shown on launch). Should only be one of these.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    def __init__(self, root):
        super().__init__("Main Window", root)
        hwCntrl.setScope() #Reset scope to make sure schedule is running
        self.lightToggleModes = ['Schedule', 'All On', 'All Night', 'All Off']
        self.currentLightToggleModeInx = 0

        self.lightModeText = tk.StringVar()
        self.lightModeText.set(self.lightToggleModes[self.currentLightToggleModeInx])
        #self.lightModeText.place(x=10, y=5)

        self.tempText = tk.StringVar()
        self.tempText.set(f"Temperature\n???°F")

        self.phText = tk.StringVar()
        self.phText.set(f"pH\n???")


        buttons = [
            ["Toggle Lights\nDay/Night/Off/\nSchedule", self.toggle_lights],
            [self.tempText, lambda: TemperaturePage()],
            [self.phText, lambda: PhPage()],
            ["Manual\nFertilizer", lambda: ManualFertilizerPage()],
            ["Settings", lambda: SettingsPage()]
        ]

        self.drawButtonGrid(buttons)

        #After we're done setting everything up...
        self.refresh_data()

    def toggle_lights(self):
        self.currentLightToggleModeInx = (self.currentLightToggleModeInx + 1) % len(self.lightToggleModes)

        myScope = 'gui'
        newMode = self.lightToggleModes[self.currentLightToggleModeInx]
        print(f"Toggled to mode {newMode}", flush=True)
        if (newMode == 'Schedule'):
            hwCntrl.setScope()
        elif (newMode == 'All On'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2,3]:
                hwCntrl.setLightState(lightId, hardwareControl_pb2.LightState_Day, scope=myScope)

        elif (newMode == 'All Night'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2,3]:
                hwCntrl.setLightState(lightId, hardwareControl_pb2.LightState_Night, scope=myScope)

        elif (newMode == 'All Off'):
            hwCntrl.setScope(scope=myScope)
            for lightId in [1,2,3]:
                hwCntrl.setLightState(lightId, hardwareControl_pb2.LightState_Off, scope=myScope)


    def refresh_data(self):
        now = datetime.datetime.now()
        print(f"refreshing at {now}", flush=True)

        #Update all things that need updating

        #Update the temperature reading
        temp_degC = hwCntrl.getTemperature_degC()
        temp_degF = (temp_degC * 9.0) / 5.0 + 32.0
        self.tempText.set(f"Temperature\n{temp_degF:0.2f}°F")

        #Update the pH Reading
        ph = hwCntrl.getPH()
        self.phText.set(f"pH\n{ph:0.2f}")


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

        buttons = [
            ["Reboot", self.dummy],
            ["Aquarium\nLights", self.dummy],
            ["Grow Lights", self.dummy],
            ["Fertilizer", self.dummy],
            ["Calibrate pH", self.dummy],
            ["System Settings", lambda: SystemSettingsPage()]
        ]

        self.drawButtonGrid(buttons)



class SystemSettingsPage(Subwindow):

    def __init__(self):
        super().__init__("System Settings")

        tk.Label(self.master, text=f"IP Address: {get_ip()}", font=("Arial", 10)).grid(row=1, column=0, padx=5, pady= 5)
        tk.Label(self.master, text=f"", font=("Arial", 10)).grid(row=2, column=0)
        tk.Label(self.master, text=f"", font=("Arial", 10)).grid(row=3, column=0)


        buttons = [
            ["About", self.dummy],
            ["Shutdown", self.dummy],
            ["Exit GUI", self.quitGui],
            ["Network Info", self.dummy],
            ["Set Time", self.dummy],
            ["Restore\nDefaults", self.dummy]
        ]

        self.drawButtonGrid(buttons)


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

        buttons = [
            ["Dispense\n3mL",lambda: self.dispenseInThread(1)],
            ["Dispense\n10mL", lambda: self.dispenseInThread(1)],
            ["Prime Line\nPush to start", None],
            ["Timer\nSettings", lambda:SettingsPage()]
        ]
        self.drawButtonGrid(buttons)

        self.buttons[2].bind("<ButtonPress>", self.on_press)
        self.buttons[2].bind("<ButtonRelease>", self.on_release)

    def on_press(self, event):
        self.dispense_stop_event = threading.Event()
        self.dispenseThread = threading.Thread(target=dispense, args=(hwCntrl, 50, self.dispense_stop_event), daemon=True)
        self.dispenseThread.start()


    def on_release(self, event):
        if (self.dispenseThread.is_alive()):
            self.dispense_stop_event.set()
            self.dispenseThread.join()
            print("Dispense thread killed", flush=True)
        else:
            self.dispenseThread.join()
            print("Dispense thread already dead", flush=True)


    def dispenseInThread(self, volume_ml):
        stop_event = threading.Event()
        self.thread = threading.Thread(target=dispense, args=(hwCntrl, volume_ml, stop_event), daemon=True)
        self.thread.start()
        self.thread.join()



    def primeToggle(self):
        pass


if __name__ == "__main__":
    logging.basicConfig(
        filename='gui.log',
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().setLevel(logging.INFO)
    logging.info("--------- GUI RESTART-------------")

    with grpc.insecure_channel(f"{ADDRESS}:{PORT}") as channel:
        hwCntrl = HardwareControlClient(channel)
        hwCntrl.echo()
        root = tk.Tk()
        main = MainWindow(root)
        #root.attributes('-fullscreen', True) #Uncomment to make fullscreen

        root.mainloop()

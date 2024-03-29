import tkinter as tk
import weakref
from loguru import logger
import threading
import os


fontTuple = ("Arial", 15)


def activity_kick(func):
    """Decorator to make a function update watchdog"""

    def wrap(*args, **kwargs):
        Window.kick_activity_watchdog(source=func.__name__)
        result = func(*args, **kwargs)
        return result

    return wrap


class Window(object):
    """Generic window object. Do not instantiate directly.

    Parameters
    ----------
    object : [type]
        [description]
    """

    # Class Vars
    is_fullscreen = None  # class var
    main_window = None
    activity_timer = None
    activity_timeout_sec = 5.0
    activity_expiration_callback = lambda: logger.debug(  # noqa: E731
        "Default expiration callback"
    )
    wifi_callback = lambda: logger.debug("Default wifi callback")  # noqa: E731
    get_wifi_state_func = lambda: None  # noqa: E731
    lock_img = None
    wifi_on_img = None
    wifi_off_img = None

    def __init__(self, title, handle, fullscreen):
        self.master = handle
        self.master.wm_geometry("640x480")
        self.master.title(title)
        # Only store this the first time. Probably a better pattern for this.
        if Window.is_fullscreen is None:
            Window.is_fullscreen = fullscreen
        if Window.is_fullscreen:
            self.master.attributes("-fullscreen", True)

        if Window.main_window is None:
            logger.debug("Storing reference to main window")
            Window.main_window = self  # Store reference to main window

    def draw_lock_button(self):
        """_summary_

        Parameters
        ----------
        command : _type_, optional
            _description_, by default None
        """

        # Only load the lock image once per class
        if Window.lock_img is None:
            Window.lock_img = tk.PhotoImage(
                file=os.path.join(os.path.dirname(__file__), "icons", "unlock_icon.png")
            ).subsample(10, 10)

        self.lock_btn = tk.Button(
            self.master,
            image=Window.lock_img,
            command=Window.activity_expiration_callback,
        )
        self.lock_btn.place(x=32, y=10)
        self.lock_btn.configure(bg="#BBBBBB")

    def draw_wifi_indicator(self, as_button=False):
        """Draw the WiFi status indicator at the top of the window.
        If `as_button` is TRUE, it is draw as a button that when clicked goes to the NetworkSettingsPage.
        If `as_button` is FALSE, it is drawn as a static image.

        Note that the indicator will not automatically change/update based on Wifi status unless this function
        is called again.

        """
        self.wifi_is_button = as_button
        wifi_state = Window.get_wifi_state_func()

        # Only load the image once per class
        if Window.wifi_on_img is None:
            Window.wifi_on_img = tk.PhotoImage(
                file=os.path.join(
                    os.path.dirname(__file__), "icons", "wifi_on_icon.png"
                )
            ).subsample(10, 10)

        if Window.wifi_off_img is None:
            Window.wifi_off_img = tk.PhotoImage(
                file=os.path.join(
                    os.path.dirname(__file__), "icons", "wifi_off_icon.png"
                )
            ).subsample(10, 10)

        wifi_img = Window.wifi_on_img if wifi_state else Window.wifi_off_img

        if as_button:
            self.wifi_btn = tk.Button(
                self.master, image=wifi_img, command=Window.wifi_callback
            )
            self.wifi_btn.place(x=150, y=10)
            self.wifi_btn.configure(bg="#BBBBBB")
        else:
            self.wifi_label = tk.Label(self.master, image=wifi_img)
            self.wifi_label.place(x=150, y=10)

    def update_wifi_indicator(self):
        """Check current wifi status, and update button/indicator"""
        wifi_state = Window.get_wifi_state_func()
        logger.debug(f"Updating WiFi indicator (Status = {wifi_state})")
        wifi_img = Window.wifi_on_img if wifi_state else Window.wifi_off_img
        if self.wifi_is_button:
            self.wifi_btn.configure(image=wifi_img)
        else:
            self.wifi_label.configure(image=wifi_img)

    def dummy(self):
        pass

    def disable_all_buttons(self):
        for button in self.buttons:
            button["state"] = tk.DISABLED

    def enable_all_buttons(self):
        for button in self.buttons:
            button["state"] = tk.NORMAL

    def drawButtonGrid(self, buttonMap):
        """Build the standard grid of buttons

        Parameters
        ----------
        buttonMap : [type]
            [description]
        """
        self.buttons = []
        frame = tk.Frame(self.master)
        frame.place(in_=self.master, anchor="c", relx=0.5, rely=0.57)
        for inx, bInfo in enumerate(buttonMap):
            f = tk.Frame(
                frame, width=200, height=200, padx=10, pady=10
            )  # make a frame where button goes

            callback = activity_kick(
                bInfo["callback"]
            )  # Wrap the callback function with watchdog kicker

            param_dict = dict()
            param_dict["font"] = fontTuple
            param_dict["command"] = callback

            if isinstance(bInfo["text"], str):
                param_dict["text"] = bInfo["text"]
            else:
                param_dict["textvariable"] = bInfo["text"]

            if "image" in bInfo:
                param_dict["image"] = bInfo["image"]
                param_dict["compound"] = tk.TOP

            if "disable" in bInfo:
                # Don't make a button
                del param_dict["command"]
                if "text_color" in bInfo:
                    param_dict["fg"] = bInfo["text_color"]
                b = tk.Label(f, **param_dict)
            else:
                b = tk.Button(f, **param_dict)

                if "color" in bInfo:
                    b.configure(bg=bInfo["color"])
                else:
                    b.configure(bg="#BBBBBB")

            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight=1)
            f.grid_propagate(0)

            f.grid(row=int(inx / 3), column=inx % 3)
            b.grid(sticky="NWSE")
            self.buttons.append(b)

    @classmethod
    def kick_activity_watchdog(cls, source=None):
        logger.debug(f"kicking watchdog from {source}")
        if Window.activity_timer is not None:
            Window.activity_timer.cancel()
        Window.activity_timer = threading.Timer(
            Window.activity_timeout_sec, Window.activity_expiration_callback
        )
        Window.activity_timer.daemon = (
            True  # So we don't need to kill this when running exiting program
        )
        Window.activity_timer.start()

    @classmethod
    def set_activity_timeout(cls, time_sec: float):
        logger.debug(f"Set activity timeout to {time_sec}s")
        Window.activity_timeout_sec = time_sec

    @classmethod
    def set_activity_expiration_callback(cls, func):
        Window.activity_expiration_callback = func

    @classmethod
    def set_wifi_callback(cls, func):
        Window.wifi_callback = func

    @classmethod
    def set_get_wifi_state_func(cls, func):
        Window.get_wifi_state_func = func


class Subwindow(Window):
    """Generic Subwindow class. Make an inherited class from this for a custom subwindow.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    instances = weakref.WeakSet()  # Set to track all instances of Subwindow

    def __init__(
        self,
        title,
        exit_button_text="Back",
        draw_exit_button=True,
        draw_lock_button=True,
        draw_wifi_indicator=False,
    ):
        super().__init__(title, tk.Toplevel(), Window.is_fullscreen)

        Subwindow.instances.add(self)  # Add self to list of instances
        self.master.grab_set()  # Make this screen front most layer

        self.exit_btn = tk.Button(
            self.master,
            text=exit_button_text,
            font=("Arial", 15),
            width=9,
            height=2,
            bg="#ff5733",
            command=self.exit,
        )
        if draw_exit_button:
            self.exit_btn.place(x=500, y=10)

        if draw_lock_button:
            self.draw_lock_button()

        if draw_wifi_indicator:
            self.draw_wifi_indicator()

    @activity_kick
    def exit(self):
        self.master.destroy()
        self.master.update()

    @classmethod
    def get_instances(cls) -> list:
        return list(Subwindow.instances)

    @classmethod
    def destroy_all(cls):
        logger.debug("Destorying all subwindows")
        windows = cls.get_instances()
        logger.debug(str(windows))
        for w in windows:
            w.exit()


class ErrorPromptPage(Subwindow):
    """A Page to display an error message"""

    @activity_kick
    def __init__(self, msg):
        super().__init__("Error", draw_exit_button=False, draw_lock_button=False)

        buttons = [{"text": "OK", "callback": self.exit}]

        self.drawButtonGrid(buttons)

        tk.Label(self.master, text="Error", font=("Arial", 20, "bold")).pack(
            side=tk.TOP, pady=40
        )

        tk.Label(self.master, text=msg, font=("Arial", 20)).pack(side=tk.TOP, pady=10)


class ConfirmPromptPage(Subwindow):
    """A Page to confirm a request"""

    @activity_kick
    def __init__(self, msg, cmd):
        super().__init__("Confirm", draw_exit_button=False, draw_lock_button=False)

        self.cmd = cmd

        buttons = [
            {"text": "Yes", "callback": self.execute},
            {"text": "No", "callback": self.exit},
        ]

        self.drawButtonGrid(buttons)

        tk.Label(self.master, text=msg, font=("Arial", 20)).pack(side=tk.TOP, pady=40)

    def execute(self):
        self.cmd()
        self.exit()

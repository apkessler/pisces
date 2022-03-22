
import tkinter as tk
import weakref
from loguru import logger
import threading
fontTuple = ('Arial', 15)

def activity_kick(func):
    ''' Decorator to make a function update watchdog'''

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
    #Class Vars
    is_fullscreen = None #class var
    main_window = None
    activity_timer = None
    activity_timeout_sec = 5.0
    activity_expiration_callback = lambda: logger.debug("Default expiration callback")

    def __init__(self, title, handle, fullscreen):
        self.master = handle
        self.master.wm_geometry("640x480")
        self.master.title(title)
        #Only store this the first time. Probably a better pattern for this.
        if (Window.is_fullscreen == None):
            Window.is_fullscreen= fullscreen
        if (Window.is_fullscreen):
            self.master.attributes('-fullscreen', True)

        if (Window.main_window == None):
            logger.debug("Storing reference to main window")
            Window.main_window = self #Store reference to main window

    def dummy(self):
        pass

    def disable_all_buttons(self):
        for button in self.buttons:
            button['state'] = tk.DISABLED


    def enable_all_buttons(self):
        for button in self.buttons:
            button['state'] = tk.NORMAL

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
            f = tk.Frame(frame, width=200, height=200, padx=10, pady=10) #make a frame where button goes

            callback = activity_kick(bInfo['callback']) #Wrap the callback function with watchdog kicker


            if (type(bInfo['text']) is str):
                b = tk.Button(f, text=bInfo['text'], font=fontTuple, command=callback)#, disabledforeground='black')
            else:
                b = tk.Button(f, textvariable=bInfo['text'], font=fontTuple, command=callback)#, disabledforeground='black')

            if 'color' in bInfo:
                b.configure(bg=bInfo['color'])
            else:
                #b.configure(bg='#f5f5f5')
                pass


            f.rowconfigure(0, weight=1)
            f.columnconfigure(0, weight = 1)
            f.grid_propagate(0)

            f.grid(row = int(inx/3), column=inx%3)
            b.grid(sticky="NWSE")
            self.buttons.append(b)

    @classmethod
    def kick_activity_watchdog(cls, source=None):
        logger.debug(f"kicking watchdog from {source}")
        if (Window.activity_timer != None):
            Window.activity_timer.cancel()
        Window.activity_timer = threading.Timer(Window.activity_timeout_sec, Window.activity_expiration_callback)
        Window.activity_timer.daemon = True #So we don't need to kill this when running exiting program
        Window.activity_timer.start()

    @classmethod
    def set_activity_timeout(cls, time_sec:float):
        logger.debug(f"Set activity timeout to {time_sec}s")
        Window.activity_timeout_sec = time_sec


    @classmethod
    def set_activity_expiration_callback(cls, func):
        Window.activity_expiration_callback = func

class Subwindow(Window):
    """Generic Subwindow class. Make an inherited class from this for a custom subwindow.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    instances = weakref.WeakSet() #Set to track all instaces of Subwindow

    def __init__(self, title, exit_button_text="Back", draw_exit_button=True):
        super().__init__(title, tk.Toplevel(), Window.is_fullscreen)

        Subwindow.instances.add(self) #Add self to list of instances
        self.master.grab_set() #Make this screen front most layer

        self.exit_btn = tk.Button(self.master, text=exit_button_text, font=('Arial', 15), width=9, height=2, bg='#ff5733', command=self.exit)
        if (draw_exit_button):
            self.exit_btn.place(x=450, y=10)

    @activity_kick
    def exit(self):
        self.master.destroy()
        self.master.update()

    @classmethod
    def get_instances(cls) -> list:
        return list(Subwindow.instances)

    @classmethod
    def destroy_all(cls):
        logger.debug('Destorying all subwindows')
        windows = cls.get_instances()
        logger.debug(str(windows))
        for w in windows:
            w.exit()



class ErrorPromptPage(Subwindow):
    ''' A Page to display an error message'''
    def __init__(self, msg):
        super().__init__("Error", draw_exit_button=False)

        buttons = [
            {'text': "OK",     'callback': self.exit}
        ]

        self.drawButtonGrid(buttons)

        tk.Label(self.master,
        text="Error",
        font=('Arial', 20, 'bold')).pack(side=tk.TOP, pady=40)

        tk.Label(self.master,
        text=msg,
        font=('Arial', 20)).pack(side=tk.TOP, pady=10)


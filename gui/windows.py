
import tkinter as tk
fontTuple = ('Arial', 15)


class Window(object):
    """Generic window object. Do not instantiate directly.

    Parameters
    ----------
    object : [type]
        [description]
    """
    is_fullscreen = None #class var

    def __init__(self, title, handle, fullscreen):
        self.master = handle
        self.master.wm_geometry("640x480")
        self.master.title(title)
        #Only store this the first time. Probably a better pattern for this.
        if (Window.is_fullscreen == None):
            Window.is_fullscreen= fullscreen
        if (Window.is_fullscreen):
            self.master.attributes('-fullscreen', True)


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
            f = tk.Frame(frame, width=200, height=200, padx=10, pady=10) #make a frame where button goes



            if (type(bInfo['text']) is str):
                b = tk.Button(f, text=bInfo['text'], font=fontTuple, command=bInfo['callback'])
            else:
                b = tk.Button(f, textvariable=bInfo['text'], font=fontTuple, command=bInfo['callback'])

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



class Subwindow(Window):
    """Generic Subwindow class. Make an inherited class from this for a custom subwindow.

    Parameters
    ----------
    Window : [type]
        [description]
    """

    def __init__(self, title, exit_button_text="Back", draw_exit_button=True):
        super().__init__(title, tk.Toplevel(), Window.is_fullscreen)

        self.master.grab_set()

        self.exit_btn = tk.Button(self.master, text=exit_button_text, font=('Arial', 15), width=9, height=2, bg='#ff5733', command=self.exit)
        if (draw_exit_button):
            self.exit_btn.place(x=450, y=10)

    def exit(self):
        self.master.destroy()
        self.master.update()


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


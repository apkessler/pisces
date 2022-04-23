
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Class for interactive Graphs of data
"""

# Standard imports
import datetime
from dateutil import relativedelta

# 3rd party imports
import tkinter as tk
import pandas as pd
from loguru import logger

#Plotting imports
import matplotlib as plt
from matplotlib.figure import (Figure, )
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.ticker import (FormatStrFormatter, FuncFormatter)
import matplotlib.dates as mdates


# Custom imports
from helpers import *
from windows import (Subwindow, ErrorPromptPage, fontTuple, activity_kick)


class GraphPage(Subwindow):

    def __init__(self, field:str, jData:dict):
        super().__init__(field, draw_exit_button=False, draw_lock_button=False)

        self.jData= jData
        #Read in the dataframe and parse timestamp strings to datetime
        self.df = pd.read_csv(jData['telemetry_file'], parse_dates=["Timestamp"])

        #Set the index to timestamp column so we can index by it
        self.df['Timestamp'] = self.df['Timestamp'].dt.round('60min') #Rounding to the nearest hour makes x-axis auto labelling cleaner
        self.df.set_index('Timestamp', inplace=True)
        logger.info(f'Dataset ranges from {self.df.index.min()} to {self.df.index.max()}')

        #Pull the safe hi/lo bounds to plot horz lines from config file
        try:
            self.settings = jData['graph_settings'][field]
        except KeyError:
            logger.error(f'Bad Graph Type "{field}"')
            self.exit()



        self.fig = Figure(figsize=(10,4), dpi = 100)
        self.ax = self.fig.add_subplot()

        self.field = field

        top = tk.Frame(self.master)
        bottom = tk.Frame(self.master)
        top.pack(side=tk.TOP)
        bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


        self.canvas = FigureCanvasTkAgg(self.fig, master=bottom) # A tk.DrawingArea
        self.canvas.draw()


        #By default, show the last week of data
        self.max_time_to_plot = self.df.index.max() #Rather than use actual "now" timestamp, use the last piece of data in log

        self.ONE_WEEK = datetime.timedelta(days=7)
        #Using relative deltas for these deals with leap years, shorter months, etc.
        self.ONE_MONTH = relativedelta.relativedelta(months=1)
        self.ONE_YEAR = relativedelta.relativedelta(years=1)



        # pack_toolbar=False will make it easier to use a layout manager later on.
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.master, pack_toolbar=False)
        self.toolbar.update()


        #We need to manually recreate the Back button since it got wiped by the matplotlib canvas
        self.back_btn = tk.Button(self.master, text="Back", font=fontTuple, width=9, height=2, bg='#ff5733', command=self.exit)
        self.prev_btn = tk.Button(self.master, text="Back 1\n???", command=self.show_previous,  bg='#BBBBBB', font=fontTuple, width=9, height=2)

        this_week_btn = tk.Button(self.master, text="This\nWeek", command=self.show_this_week,  bg='#BBBBBB', font=fontTuple, width=9, height=2)
        this_month_btn = tk.Button(self.master, text="This\nMonth", command=self.show_this_month, bg='#BBBBBB', font=fontTuple, width=9, height=2)
        this_year_btn = tk.Button(self.master, text="This\nYear", command=self.show_this_year,  bg='#BBBBBB', font=fontTuple, width=9, height=2)

        self.next_btn = tk.Button(self.master, text="Forward 1\n???", command=self.show_next, bg='#BBBBBB', font=fontTuple, width=9, height=2)



        # Packing order is important. Widgets are processed sequentially and if there
        # is no space left, because the window is too small, they are not displayed.
        # The canvas is rather flexible in its size, so we pack it last which makes
        # sure the UI controls are displayed as long as possible.

        self.prev_btn.pack(in_=top, side=tk.LEFT)


        this_week_btn.pack(in_=top, side=tk.LEFT)
        this_month_btn.pack(in_=top, side=tk.LEFT)
        this_year_btn.pack(in_=top, side=tk.LEFT)

        self.next_btn.pack(in_=top, side=tk.LEFT)


        self.back_btn.pack(in_=top, side=tk.LEFT)
        #self.toolbar.pack(in_=bottom, side=tk.BOTTOM, fill=tk.X)

        self.show_this_week()

        self.canvas.get_tk_widget().pack(in_=bottom, side=tk.TOP, fill=tk.BOTH, expand=1)

    @activity_kick
    def show_previous(self):
        if self.mode == 'week':
            self.show_previous_week()
        elif self.mode == 'month':
            self.show_previous_month()
        elif (self.mode == 'year'):
            self.show_previous_year()
        else:
            logger.error(f'Unknown date mode "{self.mode}"')


    @activity_kick
    def show_next(self):
        if self.mode == 'week':
            self.show_next_week()
        elif self.mode == 'month':
            self.show_next_month()
        elif (self.mode == 'year'):
            self.show_next_year()
        else:
            logger.error(f'Unknown date mode "{self.mode}"')

    def set_mode(self,m:str):
        self.mode = m
        self.next_btn.configure(text = f'Forward 1\n{m.capitalize()}')
        self.prev_btn.configure(text = f'Back 1\n{m.capitalize()}')

    def show_previous_week(self):
        ''' Move the plotting window back 7 days. Reject if the latest time on the plot (right-hand side)
        is before the oldest data in our log (i.e. nothing would be plotted).
        '''
        tentative_new_max = self.max_time_to_plot - self.ONE_WEEK
        tentative_new_min = tentative_new_max - self.ONE_WEEK

        if (tentative_new_max <= self.df.index.min()):
            logger.info('Cannot go back further -- RHS of plot would be before any data')
        else:
            self.max_time_to_plot = tentative_new_max
            self.plot_data(tentative_new_min, tentative_new_max)


    def show_next_week(self):
        ''' Increment the plotting window forward 7 days. Reject if the earliest time on the plot (Left-hand side)
        is after the most recent data in our log (i.e. nothing would be plotted).
        '''
        tentative_new_max = self.max_time_to_plot + self.ONE_WEEK
        tentative_new_min = tentative_new_max - self.ONE_WEEK

        now = self.df.index.max() #Rather than use actual "now" timestamp, use the last piece of data in log
        if (tentative_new_min >= now):
            logger.info(f'Cannot go forward further -- LHS of plot would be after any data.')
        else:
            self.max_time_to_plot = tentative_new_max
            self.plot_data(tentative_new_min, tentative_new_max)

    def show_previous_month(self):
        ''' Move the plotting window back 1 month. Reject if the latest time on the plot (right-hand side)
        is before the oldest data in our log (i.e. nothing would be plotted).
        '''
        tentative_new_max = get_end_of_month(self.max_time_to_plot - self.ONE_MONTH) #New right hand side of x-axis
        tentative_new_min = get_start_of_month(self.max_time_to_plot - self.ONE_MONTH) #New left hand side of x-axis

        if (tentative_new_max <= self.df.index.min()):
            logger.info('Cannot go back further -- RHS of plot would be before any data')
        else:
            self.max_time_to_plot = tentative_new_max
            self.plot_data(tentative_new_min, tentative_new_max)


    def show_next_month(self):
        '''Move plotting window forward 1 month. Reject if the earliest time on the plot (Left-hand side)
        is after the most recent data in our log (i.e. nothing would be plotted).
        '''
        tentative_new_max = get_end_of_month(self.max_time_to_plot + self.ONE_MONTH) #New right hand side of x-axis
        tentative_new_min = get_start_of_month(self.max_time_to_plot + self.ONE_MONTH) #New left hand side of x-axis


        now = self.df.index.max() #Rather than use actual "now" timestamp, use the last piece of data in lpg
        if (tentative_new_min >= now):
            logger.info(f'Cannot go forward further -- LHS of plot would be after any data.')
        else:
            self.max_time_to_plot = tentative_new_max
            self.plot_data(tentative_new_min, tentative_new_max)


    def show_previous_year(self):
        ''' Move the plotting window back 1 year. Reject if the latest time on the plot (right-hand side)
        is before the oldest data in our log (i.e. nothing would be plotted).
        '''
        tentative_new_max = get_end_of_year(self.max_time_to_plot - self.ONE_YEAR) #New right hand side of x-axis
        tentative_new_min = get_start_of_year(self.max_time_to_plot - self.ONE_YEAR) #New left hand side of x-axis

        if (tentative_new_max <= self.df.index.min()):
            logger.info('Cannot go back further -- RHS of plot would be before any data')
        else:
            self.max_time_to_plot = tentative_new_max
            self.plot_data(tentative_new_min, tentative_new_max)


    def show_next_year(self):
        '''Move plotting window forward 1 year. Reject if the earliest time on the plot (Left-hand side)
        is after the most recent data in our log (i.e. nothing would be plotted).
        '''
        tentative_new_max = get_end_of_year(self.max_time_to_plot + self.ONE_YEAR) #New right hand side of x-axis
        tentative_new_min = get_start_of_year(self.max_time_to_plot + self.ONE_YEAR) #New left hand side of x-axis


        now = self.df.index.max() #Rather than use actual "now" timestamp, use the last piece of data in lpg
        if (tentative_new_min >= now):
            logger.info(f'Cannot go forward further -- LHS of plot would be after any data.')
        else:
            self.max_time_to_plot = tentative_new_max
            self.plot_data(tentative_new_min, tentative_new_max)


    @activity_kick
    def show_this_week(self):
        ''' Show the most recent 7 day's worth of data.
        '''
        now = self.df.index.max()
        self.max_time_to_plot = now

        self.set_mode('week')
        self.plot_data(self.max_time_to_plot - self.ONE_WEEK, self.max_time_to_plot)


    @activity_kick
    def show_this_month(self):
        ''' Show this month
        '''
        now = self.df.index.max()
        self.max_time_to_plot = now

        self.set_mode('month')
        self.plot_data(get_start_of_month(now), get_end_of_month(now))


    @activity_kick
    def show_this_year(self):
        ''' Show the past year
        '''
        now = self.df.index.max()
        self.max_time_to_plot = now

        self.set_mode('year')
        self.plot_data(get_start_of_year(now), get_end_of_year(now))



    def plot_data(self, start_time:datetime.datetime, end_time:datetime.datetime):
        ''' Actually plot the data in `self.df` between `start_time` and `end_time`

        Parameters
        ----------
        start_time : datetime.datetime
            The beginning the data range
        end_time : datetime.datetime
            The end of the data range
        '''
        plt.rcParams.update({'font.size': 24})


        self.ax.cla()
        logger.info(f'Plotting between {start_time} and {end_time}')
        try:
            sub_df = self.df[start_time: end_time]
            #sub_df.plot(y=[self.field], ax=self.ax)
            self.ax.plot(sub_df.index, sub_df[self.field])
        except KeyError:
            logger.error("Could not grab dates of interest from telemetry file")
            ErrorPromptPage("Oops! Looks like the telemetry file got corrupted.\nRepair of file attemped...\nPlease retry.")
            self.repair_telemetry_file()
            self.exit()
            return

        if (self.settings['yaxis_warnings'] != None):
            #If there are warning lines, draw them
            self.ax.hlines(
                y=self.settings['yaxis_warnings'],
                xmin=[start_time],
                xmax=[end_time],
                colors='red',
                linestyles='--',
                lw=1)

        self.ax.yaxis.set_major_formatter(FormatStrFormatter(self.settings['formatter']))

        #Decide on y-axis limits
        min_val = sub_df[self.field].min()
        max_val = sub_df[self.field].max()
        the_range = max_val - min_val
        if (the_range < self.settings['yaxis_min_range']):
            the_range = self.settings['yaxis_min_range']

        month_fmt = mdates.DateFormatter('%b')
        def m_fmt (x, pos=None):
            return month_fmt(x)[0]

        day_fmt = mdates.DateFormatter('%d')
        def d_fmt (x, pos=None):
            return day_fmt(x)

        buffer = self.settings['yaxis_buffer_factor']*the_range
        yrange = [min_val - buffer, max_val + buffer]
        yrange_rounded = [round(x,1) for x in yrange]
        logger.debug(f'Values in this window: [{min_val}, {max_val}] --> {yrange} --> {yrange_rounded}')
        self.ax.set_ylim(yrange_rounded)
        self.ax.set_xlim([start_time, end_time])
        self.ax.set_xlabel('')
        if (self.mode == 'week'):
            self.ax.xaxis.set_major_locator(mdates.DayLocator())
            self.ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(self.ax.xaxis.get_major_locator()))
            self.ax.set_title('Week of ' + start_time.strftime('%b %d %Y'))

        elif (self.mode == 'month'):
            self.ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.SU)) #Tick on Sundays every week
            self.ax.xaxis.set_major_formatter(FuncFormatter(d_fmt))
            self.ax.set_title(start_time.strftime('%b %Y'))

        elif (self.mode == 'year'):
            self.ax.xaxis.set_major_locator(mdates.MonthLocator())
            self.ax.xaxis.set_major_formatter(FuncFormatter(m_fmt))
            self.ax.set_title(start_time.strftime('%Y'))


        self.ax.grid(which='both')
        #self.ax.get_legend().remove()
        self.fig.subplots_adjust(bottom=0.18, left=0.14)
        self.canvas.draw()

    def repair_telemetry_file(self):
        '''
        Attempt repairs of telemetery file. Specifically, sort entries by time
        '''
        logger.info("Attempting repair of telemetry file...")

        #Read in the dataframe and parse timestamp strings to datetime
        self.df = pd.read_csv(self.jData['telemetry_file'], parse_dates=["Timestamp"])

        #Set the index to timestamp column so we can index by it
        self.df.set_index('Timestamp', inplace=True)

        #Sort by dates
        self.df.sort_index(inplace=True)

        #Send back to file
        self.df.to_csv(self.jData['telemetry_file'])



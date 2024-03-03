#!/usr/bin/env python
# -*- coding: utf-8 -*-


import csv
import datetime
import random
import pandas as pd
import matplotlib.pyplot as plt


def generate_data():
    """
    Make some fake fata
    """
    with open("telemetry.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Temperature (F)", "pH"])
        the_time = datetime.datetime(2017, 3, 10, 0)
        dt = datetime.timedelta(hours=1)
        temp = 77.0
        ph = 7.8
        while the_time < datetime.datetime.now():
            temp += 0.05 * (random.random() - 0.5)
            ph += 0.005 * (random.random() - 0.5)
            writer.writerow([the_time, round(temp, 2), round(ph, 2)])
            the_time += dt


def plot_data(df):
    df.plot()
    plt.gcf().autofmt_xdate()
    plt.show()

    # plt.savefig('plot.png')


def main():
    print("Generating data...", flush=True)
    generate_data()
    print("Generated data!", flush=True)

    # Read in the dataframe and parse timestamp strings to datetime
    df = pd.read_csv("telemetry.csv", parse_dates=["Timestamp"])

    # Set the index to timestamp column so we can index by it
    df.set_index("Timestamp", inplace=True)

    # print(df["2022-02-02":"2022-02-04"])

    # print(df)
    plot_data(df)


if __name__ == "__main__":
    main()

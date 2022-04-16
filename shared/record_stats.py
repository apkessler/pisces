#!/usr/bin/env python

'''
This script is responsible for logging tank stats (temperature, pH) to a running log file.
This function should be invoked by a cron job or similar
'''

import grpc
import csv
import datetime
import os
import argparse
from loguru import logger
from hwcontrol_client import HardwareControlClient

def main():

    parser = argparse.ArgumentParser(description='Append telemetry data to running log file.')
    parser.add_argument('filepath', help='File to append to.')

    args = parser.parse_args()

    #Open connection to HardwareControl server, and read relevant data
    with grpc.insecure_channel('localhost:50051') as channel:
        hwCntrl = HardwareControlClient(channel)
        try:
            the_temp_F = hwCntrl.getTemperature_degF()
            the_pH = hwCntrl.getPH()
        except grpc.RpcError as rpc_error:
            logger.error(f"Unable to connect to server! {rpc_error.code()}")
            exit() #Just quit, don't bother adding anything to log file

    #Now append to running log file...

    #Check if file exists already - if not, we will add a column header.
    if (os.path.isfile(args.filepath)):
        add_header = False
    else:
        logger.info("File does not exist! Will add header.")
        add_header = True


    with open(args.filepath, 'a', newline='') as statsfile:
        csvwriter = csv.writer(statsfile, delimiter=',')
        if (add_header):
            csvwriter.writerow(["Timestamp", "Temperature (F)", "pH"])
        csvwriter.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), round(the_temp_F,2), round(the_pH,2)])



if __name__ == '__main__':
    main()
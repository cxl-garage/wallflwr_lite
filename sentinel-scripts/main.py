##### Tyto AI: Conservation X Labs   #####
## Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future

"""
This script is the main process that controls the Sentinel Device in the field
"""

import sys
import os
import io
import time
import utils
#import lora
#import desmodus_draculae
import numpy as np
import csv
import shutil
from datetime import datetime
from time import strftime
import argparse
from time import process_time
import cloud_data
import cloud_db
import pandas as pd
import requests
import logging

## Setting relative path (necessary for backseat driving)
try:
    os.chdir("/home/pi/wallflwr_lite/sentinel-scripts")
except:
    os.chdir("/home/mendel/wallflwr_lite/sentinel-scripts")

logger = logging.getLogger('main')

parser = argparse.ArgumentParser()
parser.add_argument('--test', action='store_true', help='Use onboard test data rather than SD card')
parser.add_argument('--lora_off', action='store_true', help='Disable LoRa')
parser.add_argument('--gcs_off', action='store_true', help='Disable Upload of Pictures')
parser.add_argument('--sql_off', action='store_true', help='Disable Upload to SQL DB')
parser.add_argument('--update_off', action='store_true', help='Disable update of algorithms')
parser.add_argument('--type', type=str, default='int8_edgetpu', help='type of model')
parser.add_argument('--tpu_off', action='store_true', help='Turn off TPU (just run on CPU)')
parser.add_argument('--text', action='store_true', help='Send text notification')
parser.add_argument('--email', action='store_true', help='Send email notification')
opt = parser.parse_args()
#logger.info(opt)


######## BEGINNING OF THE WORK ########

# Initialize the device (check that local device is ready)
data_directory = utils.initialize(opt)
import edge_process
if os.environ.get('version').startswith('0'):
    import digitalio
    import board
    from digitalio import DigitalInOut, Direction, Pull

    # Pull the M0 Pin Low to keep the Pi on...
    shutdown_pin  = DigitalInOut(board.D14)
    shutdown_pin.direction = Direction.OUTPUT
    shutdown_pin.value = True

# Reading in information about algorithms that have to run on device
primary_algs = pd.read_csv('../models/_primary_algs.txt')
secondary_algs = pd.read_csv('../models/_secondary_algs.txt')

if len(os.listdir(data_directory)) == 0:
    logger.warning('No files to process')

## Process data until there are no data left in the data directory
#while len(os.listdir(data_directory)) != 0:

## Running loop of all algorithms that have to run on device
k = 0
while k < len(primary_algs):
    primary_alg = primary_algs.iloc[[k]]
    logger.info('Model {} Starting'.format(primary_alg['alg_id'][0]))

    # Run Primary ALgorithm
    primary_df = edge_process.main(primary_alg,data_directory,opt.type)
    logger.info('Model {} Complete'.format(primary_alg['alg_id'][0]))

    # Run Secondary Model (if it exists)
    #if len(secondary_algs)! :
    #    secondary_df = edge_process.main(secondary_algs,data_directory,opt.type)
        #print('Insert outcome from secondary model:')# secondary_class, secondary_confidence)

    k = k+1

# Delete all processed files from SD Card
utils.delete_files()

# Run LoRa Routine
#lora.main()

# If internet connection exists, upload data to cloud
if connect() == True:

    # Upload metadata to SQL database
    if opt.sql_off == False:
        cloud_db.insights()

    # Upload images to Google Cloud Storage
    if opt.gcs_off == False:
        cloud_data.upload_images()

    # Send email notification (if requested by SQL table eventually)
    if opt.email ==True:
        cloud_data.notification(type=email)

    # Send text notification (if requested by SQL table eventually)
    if opt.text ==True:
        cloud_data.notification(type=text)

else:
    logger.warning('Unable to upload to SQL/Google Cloud Storage')

## Shut down Raspberry Pi
if os.environ.get("cycle_time") == '1':
    utils.shutdown(os.environ.get("cycle_time"))
else:
    logger.info('Processing complete, device idling (shutdown disabled)')

##### Tyto AI: Conservation X Labs   #####
## Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future.

"""
Utils functions. (Functions that do the dirty work and may be needed by multiple scripts)
"""

import logging
import sys
import os
import io
import time
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

### Checking if device has internet access
def connect(url='http://www.google.com/', timeout=3):
    try:
        r = requests.head(url, timeout=timeout)
        return True
    except requests.ConnectionError as ex:
        #print(ex)
        return False



    ### Initialize the device (check that local device is ready)
def initialize(opt):
    f = open("../device.name", "r")
    lines = f.readlines()
    os.environ['device_name'] = lines[0].rstrip()

    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='../../logs/{}_actions.log'.format(os.environ.get("device_name")),
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logger = logging.getLogger('initialize')



    # Check local database exists
    if not os.path.exists('../data'):
        os.makedirs('../data')
    if not os.path.exists('../data/device_insights.csv'):
        logger.info('Device Insights Table Initializing!')
        x = pd.DataFrame(columns=['committed_sql','committed_images','committed_lora','insight_id','alg_id','time_stamp','class_id','class','confidence','image_id','x_min','y_min','x_max','y_max','device_id','group_id','group_confidence'])
        x.to_csv('../data/device_insights.csv')
    if not os.path.exists('../models'):
        os.makedirs('../models')
    if not os.path.exists('../data/camera'):
        os.makedirs('../data/camera')
    if not os.path.exists('../data/repo'):
        os.makedirs('../data/repo')


    # Check if device is connected to internet
    if connect() == True or opt.wilderness != True:
        logger.info('Internet Connection Successful')

        logger.info('Device Name: {}'.format(os.environ.get('device_name')))

        # Pull device info and write it to memory as a CSV
        cloud_db.device_info()

        # Pull latest master branch from git
        logger.info('Checking git for updates')
        from git import Repo
        repo = Repo('../')
        assert not repo.bare
        repo.remotes.origin.pull()
        if os.environ.get('release') == 'debug':
            logger.info('In Debug mode, Git is manually controlled!')
        else:
            k = 1
            for tag in repo.tags:
                if str(tag) == str(os.environ.get('release')):
                    checkout_tag = tag
                    checkout_commit = tag.commit.hexsha
                    if checkout_commit != repo.head.object.hexsha:
                        repo.git.checkout(checkout_commit)
                        logger.info('Checked out {} version (SHA: {})'.format(checkout_tag,checkout_commit))
                    else:
                        logger.info('Already up-to-date')
                    break
                if k == len(repo.tags):
                    logger.error('Version not known')
                    commit_to_checkout = repo.head.object.hexsha
                k = k + 1


        cloud_data.check_bucket_exists()
        if opt.update_off == False:
            logger.info('Checking for new algorithms')
            cloud_db.check_algs()



    else:
        logger.warning('Internet Connection not available')
        device_information = pd.read_csv('../_device_info.csv')
        print('Device ID: {}'.format(str(device_information['device_id'][0])))
        os.environ['device_id'] = str(device_information['device_id'][0])
        os.environ['cycle_time'] = str(device_information['cycle_time'][0])
        os.environ['sudoPW'] = 'endextinction'
        os.environ['shutdown'] = str(device_information['shutdown'][0])
        os.environ['version'] = str(device_information['version'][0])

    # Loop to run consistently run on RasPi
    if opt.test == False:
        list_of_devices = []

        for file in os.listdir('/dev'):
            if file.startswith("sd") and file.endswith("1"):
                list_of_devices.append(os.path.join("/dev", file))
        logger.info('Mounting SD card')
        k = 0
        while 1:
            m = 0
            while m < len(list_of_devices):
                mount_command = 'sudo mount {} ../data/camera'.format(list_of_devices[m])
                logger.info(mount_command)
                os.system('echo {}|sudo -S {}'.format(os.environ.get('sudoPW'), mount_command))
                if os.path.isdir('../data/camera/DCIM') == True:
                    logger.info('SD Card Mounted')
                    break
                m = m + 1
            if k == 3:
                logger.error('SD Card Not Found')
                shutdown(0)
            if os.path.isdir('../data/camera/DCIM') == True:
                break
            else:
                time.sleep(1)
            k = k + 1
            time.sleep(1)
        data_directory = '../data/camera/DCIM/{}'.format(os.listdir('../data/camera/DCIM/')[0])
    else:
        data_directory = '../data/test'
        logger.warning('Running in test mode')
    os.environ['data_directory'] = data_directory
    return data_directory



### Deletes files from SD Card
def delete_files():
    logger = logging.getLogger('deleter')
    # Load local insights "database" (currently just a csv) as a pandas dataframe
    insights = pd.read_csv('../data/device_insights.csv')

    # Begin loop to delete files as listed in the local database as processed
    k = 0
    while k < len(insights):
        try:
            delete_command = 'sudo rm -f {}/{}'.format(os.environ.get('data_directory'),insights['image_id'][k])
            os.system('echo {}|sudo -S {}'.format(os.environ.get('sudoPW'), delete_command))
        except Exception as e:
            logger.warning('Issue deleting file')
        k = k+1
    logger.info('Files Deleted')

### Function to make the RPi shut itself down
def shutdown(cycle_time):
    logger = logging.getLogger('shutter')
    if os.environ.get('version').startswith('0'):
        import digitalio
        import board
        from digitalio import DigitalInOut, Direction, Pull

        # Pull the M0 Pin Low to keep the Pi on...
        shutdown_pin  = DigitalInOut(board.D14)
        # Pull the M0 Pin low to communicate sleep length...
        shutdown_pin.value = False
        logger.info('Send command to M0 to shut down')
        time.sleep(int(cycle_time)/100)
        shutdown_pin.value = True

        # Pull the M0 Pin low to begin shutdown sequence...
        time.sleep(0.2)
        shutdown_pin.value = False

        # Switching pin to check for confirmation from M0 shutdown
        shutdown_pin.switch_to_input(pull=digitalio.Pull.DOWN)

        # Loop to check for confirmation from M0.
        k = 0
        while 1:
            # Scenario 1: M0 Confirmation when pin goes high, stopping shutdown
            if shutdown_pin.value == True:
                logger.warning('M0 Intervention with Shutdown')
                time.sleep(3)
                break
            # Scenario 2: Timeout
            elif k == 5:
                logger.info('M0 Timneout')
                # Shut down the logger
                logger.info('Shutting Down')
                ## Shutting Down the Pi (M0 is supposed to wait 10 seconds to shutdown
                os.system('echo {}|sudo -S sudo shutdown'.format(os.environ.get('sudoPW')))
            else:
                time.sleep(1)
            k = k + 1

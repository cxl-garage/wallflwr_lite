##### Tyto AI: Conservation X Labs   #####
# Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future
import utils
from sqlalchemy import update
import os
import logging
import datetime
import pathlib
import pandas as pd
import sqlalchemy
from sqlalchemy.types import Integer
import uuid
import time
import numpy as np
import os.path
from os import path
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
import argparse
import requests


def upload():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wilderness', action='store_true',
                        help='No internet scenario')
    parser.add_argument('--preventShutdown', action='store_true',
                        help='prevent shutdown')
    opt = parser.parse_args()

    # Read the CSV to gather the cycline time and shutdown
    device_information = pd.read_csv('../_device_info.csv')
    cycle_time = device_information['cycle_time'][0]
    shutdown = device_information['shutdown'][0]

    # Some setting up
    Base = declarative_base()
    filePath = pathlib.Path().absolute()
    logger = logging.getLogger('upload_log')
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    logging.info(shutdown)

    # Check to see if the log exists as a error failsafe
    file = pathlib.Path('{}/logs/fullLog.out'.format(filePath))
    file_list = os.listdir('{}/logs'.format(filePath))
    for x in file_list:
        print(x)
    print(file_list)
    # if file.exists():
    #     print("File exist")
    #     # Get Device ID
    #     f = open("../device.id", "r")
    #     lines = f.readlines()
    #     device_id = lines[0].rstrip()
    #     logger.info(device_id)

    #     # Rename the log to current time
    #     dt_string = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    #     logger.info(dt_string)
    #     os.rename('{}/logs/fullLog.out'.format(filePath),
    #               '{}/logs/{}.out'.format(filePath, dt_string))

    #     # Upload log if internet is connected

    #     # Get list of all files in log folder
    #     # Iterate through them and upload them

    #     # if opt.wilderness != True:
    #     #     logger.info('Uploading log')
    #     #     query = 'gsutil -m cp -r -n "./logs/{}.out" "gs://insights-{}/logs/"'.format(
    #     #         dt_string, device_id)
    #     #     result = os.system(query)
    #     #     if 0 == result:
    #     #         logging.info("upload complete")
    #     #     else:
    #     #         logging.info("result code: %d" % result)
    #     #     # Remove log
    #     #     os.remove('{}/logs/{}.out'.format(filePath, dt_string))
    # else:
    #     print("File not exist")

    # Shut down Raspberry Pi
    if shutdown == 1 or opt.preventShutdown != False:
        utils.shutdown(cycle_time)


if __name__ == "__main__":
    upload()

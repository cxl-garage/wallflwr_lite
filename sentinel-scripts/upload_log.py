##### Tyto AI: Conservation X Labs   #####
# Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future
import utils
from sqlalchemy import update
import os
import logging
import datetime
import pathlib
import os
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


def upload():

    Base = declarative_base()

    filePath = pathlib.Path().absolute()
    logger = logging.getLogger('upload_log')
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    file = pathlib.Path('{}/logs/fullLog.out'.format(filePath))
    if file.exists():
        print("File exist")
        # Get Device ID
        f = open("../device.id", "r")
        lines = f.readlines()
        device_id = lines[0].rstrip()
        logger.info(device_id)

        # Rename
        dt_string = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        logger.info(dt_string)
        os.rename('{}/logs/fullLog.out'.format(filePath),
                  '{}/logs/{}.out'.format(filePath, dt_string))

        # Upload
        logger.info('Uploading log')
        query = 'gsutil -m cp -r -n "./logs/{}.out" "gs://insights-{}/logs/"'.format(
            dt_string, device_id)
        os.system(query)

        # Remove log
        os.remove('{}/logs/{}.out'.format(filePath, dt_string))
    else:
        print("File not exist")

    device_information = pd.read_csv('../_device_info.csv')

    cycle_time = device_information['cycle_time'][0]
    shutdown = device_information['shutdown'][0]

    # Shut down Raspberry Pi
    if shutdown != '0':
        utils.shutdown(cycle_time)


if __name__ == "__main__":
    upload()

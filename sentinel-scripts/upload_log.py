##### Tyto AI: Conservation X Labs   #####
# Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future

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

Base = declarative_base()

filePath = pathlib.Path().absolute()
logger = logging.getLogger('upload_log')
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

# Get Device ID
f = open("../device.id", "r")
lines = f.readlines()
device_id = lines[0].rstrip()
logger.info(device_id)


# # Rename
# dt_string = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
# logger.info(dt_string)
# os.rename('{}/logs/fullLog.out'.format(filePath),
#           '{}/logs/{}.out'.format(filePath, dt_string))

# # Upload
# logger.info('Uploading log')
# query = 'gsutil -m cp -r -n "./logs/{}.out" "gs://insights-{}/logs/"'.format(
#     dt_string, device_id)
# os.system(query)


# # Remove log
# os.remove('{}/logs/{}.out'.format(filePath, dt_string))

# Get device info again
db_user = os.environ.get("DB_USER")
db_pass = os.environ.get("DB_PASS")
db_name = os.environ.get("DB_NAME")
db_ip = os.environ.get("DB_PRIP")
cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
URL = 'mysql+pymysql://{}:{}@{}/{}'.format(db_user, db_pass, db_ip, db_name)
engine = sqlalchemy.create_engine(
    URL, pool_size=5, max_overflow=2, pool_timeout=30, pool_recycle=1800,)
query = "SELECT * FROM devices WHERE device_id = \'{}\'".format(
    device_id)
print(query)
device_information = pd.read_sql(query, con=engine)
print(device_information)

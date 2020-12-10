##### Tyto AI: Conservation X Labs   #####
## Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future

"""
This script is designed to allow interface between the Sentinel Device and Google Cloud Platform's various products including:
- Cloud Functions
- Google Cloud Storage

It does not include SQL database, which we currently host (11-9-2020) on Google Cloud (found on mysql.py)
"""

import os
# import time
# import numpy as np
# import sys,select
# import datetime as dt
# import csv
# import pandas as pd
# import requests
# import json
import logging
#from google.cloud import storage
#client = storage.Client()


logger = logging.getLogger('upload_log')
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

logger.info('HELLOOOO')
f = open("../device.id", "r")
lines = f.readlines()
device_id = lines[0].rstrip()
logger.info(device_id)

logger.info('Uploading log')
query = 'gsutil -m cp -r -n "./logs/fullLog.out" "gs://insights-{}/logs/"'.format(device_id)
os.system(query)

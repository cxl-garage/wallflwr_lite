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
import time
import numpy as np
import sys,select
import datetime as dt
import csv
import pandas as pd
import requests
import json
import logging
#from google.cloud import storage
#client = storage.Client()


logger = logging.getLogger('upload_log')

logger.info('HELLOOOO')
# x = 'insights-{}'.format(os.environ.get('device_id'))
# logger.info(x)

# def check_bucket_exists():
#     x = 'insights-{}'.format(os.environ.get('device_id'))
#     #try:
#     #   bucket = client.get_bucket(x)
#     #   logging.info('Bucket Exists')
#     #except:
#     #   logging.info('Bucket doesnt exist, creating now...')
#     os.system('gsutil mb gs://{}'.format(x))
#     #   bucket = client.get_bucket(x)
#     #   logging.info('Bucket Created and Confirmed')



# def upload_images():
#     logger.info('Uploading Images')
#     insights = pd.read_csv('../data/device_insights.csv')

#     x = insights[insights['committed_images'] == 0]
#     #print(x)
#     x = x[x['class'] != 'blank']
#     x = x.reset_index()
#     if len(x) == 0:
#         logger.warning('No images to upload')
#         return
#     k = 0
#     device_id = str(os.environ.get('device_id'))
#     device_name = str(os.environ.get('device_name')).replace(" ","_")

#     ## Upload all files in results folder
#     query = 'gsutil -m cp -r -n "../data/results/{}/{}/*" "gs://insights-{}/{}/{}/"'.format(int(x['alg_id'][k]),x['class'][k],device_id,int(x['alg_id'][k]),x['class'][k])
#     os.system(query)

#     ## Delete all files in the results folder
#     query = 'rm -r ../data/results/{}/{}/*'.format(x['alg_id'][k],x['class'][k])
#     os.system(query)
#     #query = 'gsutil -m cp -r -n "../data/results/{}/{}/original/*" "gs://insights-{}/{}/{}/original/"'.format(int(x['alg_id'][k]),x['class'][k],device_name,int(x['alg_id'][k]),x['class'][k])
#     #os.system(query)
#     insights.loc[insights['insight_id'] == x['insight_id'][k],'committed_images'] = 1

#     insights = insights[['committed_sql','committed_images','committed_lora','insight_id','alg_id','time_stamp','class_id','class','confidence','image_id','x_min','y_min','x_max','y_max','device_id','group_id','group_confidence']]
#     insights.to_csv('../data/device_insights.csv')


# def upload_log():
#     # device_id = str(os.environ.get('device_id'))
#     logger.info('Uploading log')
#     query = 'gsutil -m cp -r -n "log.out" "gs://insights-2/logs/"'
#     # .format(fileName,device_id)
#     os.system(query)


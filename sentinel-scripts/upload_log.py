##### Tyto AI: Conservation X Labs   #####
## Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future

import os
import logging
import datetime
import pathlib
filePath = pathlib.Path().absolute()
logger = logging.getLogger('upload_log')
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

#Get Device ID
f = open("../device.id", "r")
lines = f.readlines()
device_id = lines[0].rstrip()
logger.info(device_id)



#Rename
dt_string = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
logger.info(dt_string)
os.rename('{}/logs/fullLog.out'.format(filePath),'{}/logs/{}.out'.format( filePath, dt_string))

#Upload
logger.info('Uploading log')
query = 'gsutil -m cp -r -n "./logs/{}.out" "gs://insights-{}/logs/"'.format(dt_string,device_id)
os.system(query)


#Remove log
os.rename('{}/logs/{}.out'.format( filePath, dt_string))
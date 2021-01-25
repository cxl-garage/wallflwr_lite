##### Tyto AI: Conservation X Labs   #####
# Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future

"""
This script is designed to communicate between the SQL database hosted on Google Cloud Platform and the Sentinel Device
"""


import cloud_data
from sqlalchemy import update
import datetime
import logging
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

logger = logging.getLogger('cloud_db')

# Defining the environmental variables

os.environ['DB_USER'] = 'sentinel_devices'
os.environ['CLOUD_SQL_CONNECTION_NAME'] = 'sentinel-project-278421:us-east4:algorithm-library'
os.environ['FRAMEWORK'] = 'CXL_YoloV3_TF2_v1.0'
# os.environ['DB_PRIP']   = '35.245.49.25'
os.environ['DB_PRIP'] = '127.0.0.1:1234'
os.environ['DB_NAME'] = 'algorithm_library'
os.environ['DB_PASS'] = 'endextinction'
os.environ['USERNAME'] = 'Conservation X Labs'


# Defining all the classes!

class alg_metadata(Base):
    __tablename__ = 'alg_metadata'
    alg_id = Column(Integer, primary_key=True)
    alg_name = Column(String)
    alg_type = Column(String)
    alg_description = Column(String)
    author = Column(String)
    date_created = Column(String)
    downloads = Column(String)
    accuracy = Column(String)
    framework = Column(String)
    rating = Column(String)
    latency = Column(String)
    mAP05 = Column(String)
    alg_feature = Column(String)
    complete = Column(String)
    example_img = Column(String)
    classes = Column(String)


class devices(Base):
    __tablename__ = 'devices'
    device_id = Column(String, primary_key=True)
    device_name = Column(String)
    username = Column(String)
    location = Column(String)
    lora = Column(String)
    lte = Column(String)
    wifi = Column(String)


class deployed_algs(Base):
    __tablename__ = 'deployed_algs'
    device_id = Column(String, primary_key=True)
    alg_id = Column(Integer, primary_key=True)
    status = Column(String)
    priority = Column(String)
    primary_alg = Column(String)
    primary_class = Column(String)
    sensitivity = Column(String)
    resolution = Column(String)
    action = Column(String)


# Check Algorithms that need to be downloaded
def check_algs():

    # Pull in the environmental variables
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    db_ip = os.environ.get("DB_PRIP")
    cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
    URL = 'mysql+pymysql://{}:{}@{}/{}'.format(
        db_user, db_pass, db_ip, db_name)
    engine = sqlalchemy.create_engine(
        URL, pool_size=5, max_overflow=2, pool_timeout=30, pool_recycle=1800)
    query = "SELECT * FROM deployed_algs WHERE device_id = \'{}\'".format(
        os.environ.get('device_id'))
    alg_ids = pd.read_sql(query, con=engine)
    # logger.info(alg_ids)

    # Downloading algorithms
    if len(alg_ids) == 0:
        logger.warning('No algorithms for device')
        query = "SELECT * FROM deployed_algs WHERE device_id = \'{}\' AND status = 'Deployed' AND primary_alg IS NULL".format(
            os.environ.get('device_id'))
        primary_algs = pd.read_sql(query, con=engine)
        primary_algs.to_csv('../models/_primary_algs.txt')

        query = "SELECT * FROM deployed_algs WHERE device_id = \'{}\' AND status = 'Deployed' AND primary_alg IS NOT NULL".format(
            os.environ.get('device_id'))
        secondary_algs = pd.read_sql(query, con=engine)
        secondary_algs.to_csv('../models/_secondary_algs.txt')
        return
    else:
        # Checking for algorithms that are labelled as ready to deployment but not confirmed by device
        alg_id_download = alg_ids[alg_ids['status']
                                  == 'Deploy'].reset_index(drop=True)
        logger.info('Found {} algorithms ready for download'.format(
            len(alg_id_download)))
        k = 0

        # Looping through algorithms that are flagged for download
        while k < len(alg_id_download):

            cloud_data.download_alg(alg_id_download['alg_id'][k])

            # Creating a local labels (class) .txt file for each algorithm from the SQL table
            logger.info('Creating Labels for Algorithm')
            query = "SELECT original_label FROM search_parameters WHERE alg_id = \'{}\'".format(
                alg_id_download['alg_id'][k])
            labels = pd.read_sql(query, con=engine)
            labels.to_csv(
                '../models/{}.txt'.format(alg_id_download['alg_id'][k]), header=False, index=False)

            # Confirming that the file was actually downloaded
            if path.isfile('../models/{}-int8.tflite'.format(alg_id_download['alg_id'][k])) == True or path.isfile('../models/{}.tflite'.format(alg_id_download['alg_id'][k])) == True or path.isfile('../models/{}-f16.tflite'.format(alg_id_download['alg_id'][k])) == True or path.isfile('../models/{}-int8_edgetpu.tflite'.format(alg_id_download['alg_id'][k])) == True:
                logger.info('File Found')

                # If file was found, update the SQL table to "deployed"
                Session = sessionmaker(bind=engine)
                session = Session()
                session.query(deployed_algs).filter(deployed_algs.device_id == str(os.environ.get('device_id'))).filter(
                    deployed_algs.alg_id == str(alg_id_download['alg_id'][k])).update({'status': 'Deployed'})
                session.commit()
                session.flush()
                logger.info('Success')
            else:
                logger.warning('Algorithm was not downloaded')

            k = k+1

        # Checking for algorithms that are labelled for removal
        try:
            alg_id_download = alg_ids[alg_ids['status'] == 'Remove']
            k = 0

            # Looping through algorithms that are flagged for removal from device
            while k < len(alg_id_download):

                # Command to remove the algorithm from the device
                query = 'rm ../models/{}*'.format(alg_id_download['alg_id'])
                os.system(query)

                # Check that the file was actually deleted
                if path.isfile('{}.tflite'.format(alg_id_download['alg_id'][k])) == False:

                    # Updating the SQL database
                    Session = sessionmaker(bind=engine)
                    session = Session()
                    device_info = session.query(deployed_algs).filter(deployed_algs.device_id == str(os.environ.get(
                        'device_id'))).filter(deployed_algs.alg_id == str(alg_id_download['alg_id'][k])).update({'status': 'Removed'})
                    session.commit()
                    session.flush()
                    logger.info('Success')
                k = k + 1
        except Exception as e:
            logger.warning('Nothing to remove')

        logger.info('Saving algorithm information to .txt file locally')

        # Finding all primary algorithms that have been successfully deployed to the device
        query = "SELECT * FROM deployed_algs WHERE device_id = \'{}\' AND status = 'Deployed' AND primary_alg IS NULL".format(
            os.environ.get('device_id'))
        primary_algs = pd.read_sql(query, con=engine)
        k = 0
        while k < len(primary_algs):
            # Confirming that the file is present
            if path.isfile('../models/{}-int8.tflite'.format(primary_algs['alg_id'][k])) == True or path.isfile('../models/{}.tflite'.format(primary_algs['alg_id'][k])) == True or path.isfile('../models/{}-f16.tflite'.format(primary_algs['alg_id'][k])) == True or path.isfile('../models/{}-int8_edgetpu.tflite'.format(primary_algs['alg_id'][k])) == True:
                logger.info('File Found')
            else:
                cloud_data.download_alg(primary_algs['alg_id'][k])
            if path.isfile('../models/{}.txt'.format(primary_algs['alg_id'][k])) == True:
                logger.info('Labels Found')
            else:
                # Creating a local labels (class) .txt file for each algorithm from the SQL table
                logger.info('Creating Labels for Algorithm')
                query = "SELECT original_label FROM search_parameters WHERE alg_id = \'{}\'".format(
                    primary_algs['alg_id'][k])
                labels = pd.read_sql(query, con=engine)
                labels.to_csv(
                    '../models/{}.txt'.format(primary_algs['alg_id'][k]), header=False, index=False)
            k = k + 1
        # Saving information to csv file
        primary_algs.to_csv('../models/_primary_algs.txt')

        # Finding all secondary algorithms that have been successfully deployed to the device
        query = "SELECT * FROM deployed_algs WHERE device_id = \'{}\' AND status = 'Deployed' AND primary_alg IS NOT NULL".format(
            os.environ.get('device_id'))
        secondary_algs = pd.read_sql(query, con=engine)
        k = 0
        while k < len(secondary_algs):
            # Confirming that the file is present
            if path.isfile('../models/{}-int8.tflite'.format(secondary_algs['alg_id'][k])) == True or path.isfile('../models/{}.tflite'.format(secondary_algs['alg_id'][k])) == True or path.isfile('../models/{}-f16.tflite'.format(secondary_algs['alg_id'][k])) == True or path.isfile('../models/{}-int8_edgetpu.tflite'.format(secondary_algs['alg_id'][k])) == True:
                logger.info('File Found')
            else:
                cloud_data.download_alg(secondary_algs['alg_id'][k])
            if path.isfile('../models/{}.txt'.format(secondary_algs['alg_id'][k])) == True:
                logger.info('Labels Found')
            else:
                # Creating a local labels (class) .txt file for each algorithm from the SQL table
                logger.info('Creating Labels for Algorithm')
                query = "SELECT original_label FROM search_parameters WHERE alg_id = \'{}\'".format(
                    secondary_algs['alg_id'][k])
                labels = pd.read_sql(query, con=engine)
                labels.to_csv(
                    '../models/{}.txt'.format(secondary_algs['alg_id'][k]), header=False, index=False)
            k = k + 1
        # Saving information to csv file
        secondary_algs.to_csv('../models/_secondary_algs.txt')

        logger.info('Syncing up the SQL database')

        return


# Function to make sure that the device is self-aware even after catastrophic (except memory card) failure
# def device_info():
#     db_user = os.environ.get("DB_USER")
#     db_pass = os.environ.get("DB_PASS")
#     db_name = os.environ.get("DB_NAME")
#     db_ip   = os.environ.get("DB_PRIP")
#     cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
#     URL = 'mysql+pymysql://{}:{}@{}/{}'.format(db_user,db_pass,db_ip,db_name)
#     engine = sqlalchemy.create_engine(URL, pool_size=5,max_overflow=2,pool_timeout=60,pool_recycle=1800,)
#     query = "SELECT * FROM devices WHERE device_name = \'{}\'".format(os.environ.get('device_name'))
#     print(query)
#     device_information = pd.read_sql(query,con=engine)
#     print(device_information)
#     device_information = device_information.reset_index(drop=True)
#     device_information.to_csv('../_device_info.csv')
#     print('Device ID: {}'.format(str(device_information['device_id'][0])))
#     os.environ['device_id'] = str(device_information['device_id'][0])
#     os.environ['cycle_time'] = str(device_information['cycle_time'][0])
#     os.environ['sudoPW'] = 'endextinction'
#     os.environ['shutdown'] = str(device_information['shutdown'][0])
#     os.environ['version'] = str(device_information['version'][0])


# Download cloud insights (to check we are consistent)
def insight_check():
    logger.info('Checking consistency between cloud and device')
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    db_ip = os.environ.get("DB_PRIP")
    cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
    URL = 'mysql+pymysql://{}:{}@{}/{}'.format(
        db_user, db_pass, db_ip, db_name)
    engine = sqlalchemy.create_engine(
        URL, pool_size=5, max_overflow=2, pool_timeout=30, pool_recycle=1800,)
    local_insights = pd.read_csv('../data/device_insights.csv')
    local_insights.set_index('insight_id')
    query = "SELECT * FROM insights WHERE device_id = \'{}\'".format(
        os.environ.get('device_id'))
    cloud_insights = pd.read_sql(query, con=engine)
    cloud_insights['committed_sql'] = 1
    cloud_insights['committed_images'] = 0
    cloud_insights['committed_lora'] = 1
    cloud_insights.set_index('insight_id')
    # print(cloud_insights)
    insights = pd.concat([local_insights, cloud_insights])
    insights = insights.drop_duplicates(subset=['insight_id'], keep='first')
    insights = insights.sort_values(by=['insight_id'])
    insights = insights[['committed_sql', 'committed_lora', 'committed_images', 'insight_id', 'alg_id', 'time_stamp', 'class_id',
                         'class', 'confidence', 'image_id', 'x_min', 'y_min', 'x_max', 'y_max', 'device_id', 'group_id', 'group_confidence', 'is_from_lora']]
    print(insights)
    insights.to_csv('../data/device_insights.csv')

# Upload insights captured on device to SQL DB


def upload_insights():
    logger.info('Uploading Insights to SQL')

    # Getting the environmental variables
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    db_ip = os.environ.get("DB_PRIP")

    # Connecting to the SQL DB on Google Cloud
    cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
    URL = 'mysql+pymysql://{}:{}@{}/{}'.format(
        db_user, db_pass, db_ip, db_name)
    engine = sqlalchemy.create_engine(
        URL, pool_size=5, max_overflow=2, pool_timeout=30, pool_recycle=1800,)

    # Loading local database
    insights = pd.read_csv('../data/device_insights.csv')

    # Filtering out any already committed insights
    x = insights[insights['committed_sql'] == 0]

    # Filtering out any "blank" / generic classes
    x = x[x['class'] != 'blank']

    # Committing the insights to SQL
    try:

        # Gather the insight Ids
        # LOOK AT THIS: https://stackoverflow.com/questions/42461959/how-do-i-perform-an-update-of-existing-rows-of-a-db-table-using-a-pandas-datafra
        insightIds = x['insight_id'].values
        insightIdsString = ','.join(str(e) for e in insightIds)
        print(insightIdsString)
        # Query to delete the entries to prevent issues in inserting

        if insightIdsString:
            query = "DELETE FROM insights WHERE device_id = \'{}\' AND insight_id IN ({}) ".format(
                8, insightIdsString)
            engine.execute(query)

        x = x[['insight_id', 'device_id', 'alg_id', 'image_id', 'time_stamp', 'class_id', 'class',
               'confidence', 'x_min', 'y_min', 'x_max', 'y_max', 'group_id', 'group_confidence', 'is_from_lora']]
        x.to_sql('insights', con=engine, if_exists='append', index=False)

        # Changing the local db to reflect that these insights are now on the cloud
        insights.loc[:, 'committed_sql'] = 1
        insights.loc[:, 'committed_lora'] = 1
        insights.to_csv('../data/device_insights.csv')
        logger.info('Successfully added to SQL')
    except Exception as e:
        logger.error('Issue committing data to SQL')
        logger.error(e)


# Function to make sure that the device is self-aware even after catastrophic (except memory card) failure
def device_info():
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    db_ip = os.environ.get("DB_PRIP")
    cloud_sql_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
    URL = 'mysql+pymysql://{}:{}@{}/{}'.format(
        db_user, db_pass, db_ip, db_name)
    engine = sqlalchemy.create_engine(
        URL, pool_size=5, max_overflow=2, pool_timeout=30, pool_recycle=1800,)
    query = "SELECT * FROM devices WHERE device_id = \'{}\'".format(
        os.environ.get('device_id'))
    # print(query)
    device_information = pd.read_sql(query, con=engine)
    # print(device_information)
    device_information = device_information.reset_index(drop=True)
    device_information.to_csv('../_device_info.csv')

    # upload_insights()
    #query = "SELECT * FROM insights WHERE device_id = \'{}\'".format(os.environ.get('device_id'))
    #insights = pd.read_sql(query,con=engine)
    # print(insights)
    #insights = insights[['insight_id','alg_id','time_stamp','class_id','class','confidence','image_id','x_min','y_min','x_max','y_max','device_id','group_id','group_confidence']]
    #insights['committed_sql'] = 1
    #insights['committed_images'] = 1
    #insights['committed_lora'] = 1
    # insights.to_csv('../data/device_insights.csv')
    os.environ['device_id'] = str(device_information['device_id'][0])
    os.environ['cycle_time'] = str(device_information['cycle_time'][0])
    os.environ['sudoPW'] = 'endextinction'
    os.environ['shutdown'] = str(device_information['shutdown'][0])
    os.environ['version'] = str(device_information['version'][0])
    os.environ['release'] = str(device_information['release'][0])

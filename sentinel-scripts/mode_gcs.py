# sudo pip install gsutil

import os
import time
import numpy as np
import inquirer
import sys,select
import datetime as dt
import keyboard
from threading import Timer
import csv

def gcp_init():
    try:
        user_array = np.load('user_details.npy')
        print(user_array)
        print('Welcome back {}'.format(user_array[0]))
        toc = time.process_time()
        timeout = 2
        t = Timer(timeout,print,[''])
        t.start()
        logout = input('Press enter to change user settings...')
        t.cancel()
        if logout in locals():
            _logout = 1
            while _logout:
                logout = input('Do you want to switch accounts? (y/n) ')
                if logout == 'y':
                    gcloud_login()
                    user_array = device_setup()
                    _logout = 0
                if logout == 'n':
                    _change_alg = 1
                    while _change_alg == 1:
                        change_alg = input('Do you want to change algorithms? (y/n) ')
                        if change_alg == 'y':
                            device_setup()
                            _change_alg = 0
                        if change_alg == 'n':
                            _change_alg = 0
                        else:
                            print('Please choose y or n ')
                    _logout = 0
                else:
                    print('Please choose y or n')
        else:
            print('Lets go!')

    except IOError:
            print('Welcome new user...')
            user_array = device_setup()
            gcloud_login()
            np.save('user_details.npy',user_array)

    return user_array

def device_setup():
    name = input('Lets get set up! What is your name?: ')
    time.sleep(1)
    device_name = input('What is the name of this device? ')
    time.sleep(1)
    gcloud_login()
    another_algorithm = 1
    try:
        user_array = np.array([name, device_name])
        users_array = np.append(users_array,user_array)
    except Exception as e:
        users_array = np.array([name, device_name])
    return users_array

def gcloud_login():
    time.sleep(3)
    os.system('gcloud init')

def upload_images_drive(image,folder):
    str = 'gsutil cp {} gs://{}'.format(image,folSader)
    print(str)
    os.system(str)

def upload_images_gcp(directory,bucket):
    print(directory)
    directory_list = os.listdir(directory)
    for file in directory_list:
        filename = os.fsdecode(file)
        path = os.path.join(directory,file)
        st = os.stat(path)
        mtime = dt.datetime.fromtimestamp(st.st_mtime)
        now = dt.datetime.now()
        ago = now-dt.timedelta(minutes=1)
        if filename.endswith(".jpg") and mtime < ago:
            print(filename)
            str = 'gsutil cp {} gs://{}'.format(path,bucket)
            print(str)
            os.system(str)

def ota_algorithm(user_array):
    alg_array  = 'gsutil cp gs://cxl_tflite/{}_config.csv ../models/{}_config.csv'.format(user_array[0],user_array[0])
    os.system(alg_array)
    alg_array = np.genfromtxt('../models/{}_config.csv'.format(user_array[0]), delimeter=',')
    print(alg_array[0][:])
    bucket = ''
    directory = ''
    model  = 'gsutil cp gs://{}/{} {}'.format(algorithm_name, bucket, directory)
    labels = 'gsutil cp gs://{}/{} {}'.format(algorithm_name, bucket, directory)
    print(str)
    os.system(model)
    os.system(labels)

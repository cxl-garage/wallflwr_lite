# sudo pip install gsutil

import os
import time
import numpy as np
import inquirer
import sys,select

def gcp_init():
    try:
        user_array = np.load('user_details.npy')
        print('Welcome back {}'.format(name))
        print('Press any key to re-configure (3 seconds)')
        i,o,e = select.select([sys.stdin],[],[],3)
        if (i):
            _logout = 1
            while _logout:
                logout = input('Do you want to switch accounts? (y/n)')
                if logout == 'y':
                    gcloud_login()
                    device_setup()
                    _logout = 0
                if logout == 'n':
                    _change_alg = 1
                    while _change_alg == 1:
                        change_alg = input('Do you want to change algorithms? (y/n)')
                        if change_alg == 'y':
                            device_setup()
                            _change_alg = 0
                        if change_alg == 'n':
                            _change_alg = 0
                        else:
                            print('Please choose y or n')
                    _logout = 0
                else:
                    print('Please choose y or n')
        else:
            print('Lets go!')

    except IOError:
            user_array = device_setup()
            gcloud_login()
            np.save('user_details.npy',user_array)

    return user_array

def device_setup():
    name = input('Lets get set up! What is your name?: ')
    time.sleep(1)
    device_name = input('What is the name of this device?')
    time.sleep(1)
    another_algorithm = 1

    while another_algorithm == 1:
        primary_algorithm = input('What have you named your first algorithm (please match exactly)')
        primary_type      = inquirer.List('primary_type',
                            message='What sampling device are you using?',
                            choices=['RGB Camera','FLIR Camera','Multispec','Microphone','External Hydrophone','Temperature','IMU'])
        _series = 1
        while _series == 1:
            series    = input('Did you have an algorithm in series with {}? (y/n)'.format(algorithm))
            if series == 'y':
                secondary_algorithm = input('What have you named your first algorithm (please match exactly)')
                secondary_type      = inquirer.List('secondary_type',
                                    message='What sampling device are you using?',
                                    choices=['RGB Camera','FLIR Camera','Multispec','Microphone','External Hydrophone','Temperature','IMU'])
                _series = 0
            if series == 'n':
                secondary_algorithm = []
                secondary_type      = []
                _series = 0
            else:
                print('Please enter y or n')
        try:
            user_array = np.array([name, device_name, primary_algorithm,primary_type,secondary_algorithm,secondary_type])
            users_array = np.append(users_array,user_array)
        except Exception as e:
            users_array = np.array([name, device_name, primary_algorithm,primary_type,secondary_algorithm,secondary_type])
        _parallel =1
        while _parallel == 1:
            parallel = input('Do you want to add another algorithm?')
            if parallel == 'y':
                _parallel = 0
            if parallel == 'n':
                _parallel = 0
                another_algorithm = 0
            else:
                print('Please enter y or n')
    return users_array

def gcloud_login():
    print('Welcome {}! Lets get you securly logged into Google Cloud'.format(name))
    time.sleep(3)
    os.system('gcloud init')

def upload_images_drive(image,folder):
    str = 'gsutil cp {} gs://{}'.format(image,folder)
    print(str)
    os.system(str)

def upload_images_gcp(image,bucket):
    str = 'gsutil cp {} gs://{}'.format(image,folder)
    print(str)
    os.system(str)

def ota_algorithm(algorithm_name, bucket, directory):
    model  = 'gsutil cp gs://{}/{} {}'.format(algorithm_name, bucket, directory)
    labels = 'gsutil cp gs://{}/{} {}'.format(algorithm_name, bucket, directory)
    print(str)
    os.system(model)
    os.system(labels)

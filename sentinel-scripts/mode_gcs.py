# sudo pip install gsutil

import os
import time
import numpy as np

def gcp_init():
    try:
        user_array = np.load('user_details.npy')
        name = user_array[0]
        print('Welcome back {}'.format(name))
    except IOError:
        name = input('Lets get set up! What is your name?: ')
        time.sleep(1)
        print('Welcome {}! Lets get you securly logged into Google Cloud'.format(name))
        time.sleep(3)
        os.system('gcloud init')
        user_array = np.array([name])
        np.save('user_details.npy',user_array)

def upload_images_drive(image,folder):
    str = 'gsutil cp {} gs://{}'.format(image,folder)
    print(str)
    os.system(str)

def upload_images_gcp(image,bucket):
    str = 'gsutil cp {} gs://{}'.format(image,folder)
    print(str)
    os.system(str)

def ota_algorithm(algorithm_name, bucket, directory):
    str = 'gsutil cp gs://{}/{} {}'.format(algorithm_name, bucket, directory)
    print(str)
    os.system(str)

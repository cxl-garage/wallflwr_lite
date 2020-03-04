# sudo pip install gsutil

import os
import time

def gcp_init():
    try:
        f = open('user_details.csv')
    except IOError:
        name = input('Lets get set up! What is your name?')
        time.sleep(1)
        print('Welcome {}! Lets get you securly logged into Google Cloud')
        time.sleep(3)
        csv_file = 'user_details.csv'
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames = 'user_name')
            writer.writeheader()
            writer.writerow(name)
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
    str = 'gsutil cp gs://{}/{} {}'.format(algorithm_name, bucket, directory)
    print(str)
    os.system(str)

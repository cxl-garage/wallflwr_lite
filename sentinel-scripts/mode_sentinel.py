


## Setup (Copy stable version into _master.py)

## Script (Copy stable version into a function in stable_modes.py)
from __future__ import print_function
import argparse
import os
import shutil
import sys
import RPi.GPIO as GPIO
import time
import picamera as PiCamera
import datetime


def save_data(image,results,path,ext='jpeg'):
    tag = '%010d' % int(time.monotonic()*1000)
    name = '%simg-%s.%s' %(path,tag,ext)
    image.save(name)
    print('Frame saved as: %s' %name)
    logging.info('Image: %s Results: %s', tag,results)

def user_selections():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trigger', required=True,
                        help='Type of trigger')
    parser.add_argument('--trigger_check', required=False, default='',
                        help='Any additional trigger check methods')
    parser.add_argument('--trigger_sensitivity', required=True,
                        help='how sensitive is the trigger')
    parser.add_argument('--image_burst', required=False, default = 0,
                        help='How many images are taken immediately')
    parser.add_argument('--model_type', required=False, default = 'image',
                        help='Image, Video, Acoustics, Motion')
    parser.add_argument('--data_directory', required=True,
                        help='Where are the burst images being saved?')
    args = parser.parse_args()
    return args

def main(trigger, trigger_check, trigger_sensitivity, image_burst, \
    model_type, results_directory):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.IN)
    trigger_count = 0
    camera = PiCamera.PiCamera()
    j = 0
    # check if trigger exists, if it doesn't break this script and return to _master.py
    if trigger != 'pir':
           print('No trigger is specified, moving forward with script')
    if trigger == 'pir':
        while True :
    		#Take input from PIR sensor
                pir_status = GPIO.input(4)
    		#If no motion detected by PIR sensor
                if pir_status == 0:
                    print('No Motion')
                    trigger_count = 0
    		#If motion detected by PIR sensor
                if pir_status == 1:
                    if trigger_count > trigger_sensitivity:
                         print('Motion Detected, awaiting confirmation')
                         time.sleep(0.5)
                         j += 1
                         print(j)
                    else:
                         print('Motion Confirmed')
                         break
    burst = 0
    print('Taking photo burst')
    while burst < image_burst:
         #t_now = datetime.datetime.now.strftime("%Y%m%d%H%M%S")
         file = '_Testing_%s.jpg' %(burst)
         camera.capture(file)
         print('Pitcure Saved')
         time.sleep(1)
         burst += 1

if __name__ == "__main__":
    main()

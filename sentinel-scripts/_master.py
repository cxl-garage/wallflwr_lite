import sys
import subprocess
import os
import io
import pathlib as Path
import time
import mode_cnn
import mode_sentinel
import mode_comms
import desmodus_draculae
import numpy as np
import csv
import shutil
from datetime import datetime
from time import strftime
import argparse
from time import process_time
from mode_gcs import ota_algorithm, gcp_init

## Master Script for CXL Camera Trap Control

## Initialization

gcp_init()

primary_labels = 'models/tflite/deer_binary_v0_3/dict.txt'
primary_model = 'models/tflite/deer_binary_v0_3/model.tflite' #'models/tflite/spermwhale/spermwhale_edge_v0_1.tflite'
primary_data_directory = 'data/rgb' #'/home/sam/AI_Training/deer_train'
primary_results_directory = 'data/rgb_cropped'
secondary_labels = ''
secondary_model = ''
secondary_data_directory = 'data/flir'
secondary_results_directory = ''



trigger = 'pir'     # 'pir' or 'ir'
trigger_check = '' #'ir'    # 'ir' or 'paired_pir'
trigger_sensitivity = 6  #int between 1-100 (twenty being highest sensitivity)
camera = 'PiCamera'
t_background = ''   # int
t_lorawan = ''  # int
sys_mode = 'real' # 'real'
max_images = 5 # number of images to run in test scenario
save_cropped_im = 1
reset_results = 1
mcu = 'rpi0' # computer, rpi0
primary_format = 'coral' #coral, tf_lite,tensorflow, tflite
primary_type = 'image'
secondary_format = ''
secondary_type = ''
device_identifier = ''
comms_type = 'lora_rfm9x'
comms_backend = 'ttn'
background_subtraction = ''
current_background = ''
primary_resolution = (2592,1944)
secondary_resolution = (300,400)
primary_model_resolution = (432,324)
secondary_model_resolution = (300,400)
ai_sensitivity = 0.3
lora_counter = 0
image_burst = 1
primary_class = 99
primary_confidence = 0
secondary_class = 99
secondary_confidence = 0
clear_directories = 1
delete_directories = 1
draculae_freq = 100000
global_network = 'CXL'
local_network = 'sentinel_retrofit'


if delete_directories == 1:
    parser = argparse.ArgumentParser()
    parser.add_argument('--sensitivity', required=False, default=ai_sensitivity, \
                        help='What is the minimum CNN confidence?')
    parser.add_argument('--rgb_res', required=False, default=primary_resolution, \
                        help='Image Resolution of RGB saved photos')
    parser.add_argument('--pcnn_res', required=False, default=primary_model_resolution, \
                        help='Resolution passed through to primary CNN')
    parser.add_argument('--scnn_res', required=False, default=secondary_model_resolution, \
                        help='Resolution passed through to primary CNN')
    parser.add_argument('--primary_type', required=False, default='image',
                        help='Image, Video, Acoustics, Motion')
    parser.add_argument('--secondary_type', required=False, default='image',
                        help='Image, Video, Acoustics, Motion')
    args = parser.parse_args()



if sys_mode == 'test':
    print('Mode: Test')
if sys_mode == 'real':
    print('Mode: Real')
    if mcu == 'computer':
        print('Cannot run "real" mode from mcu/vpu = computer')
    if mcu == 'rpi0':
        primary_labels = os.path.join('../',primary_labels)
        primary_model  = os.path.join('../',primary_model)
        primary_data_directory = os.path.join('../', primary_data_directory)
        primary_results_directory = os.path.join('../', primary_results_directory)
        secondary_labels = os.path.join('../', secondary_labels)
        secondary_labels = os.path.join('../',secondary_model)
        secondary_data_directory = os.path.join('../', secondary_data_directory)
        secondary_results_directory = os.path.join('../', secondary_results_directory)
        #primary_format = args.primary_format
        #secondary_format = args.secondary_format
        #primary_type = args.primary_type
        #secondary_type = args.secondary_type
        #print('Real Scenario running on RPi Zero')
    if not os.path.exists(primary_data_directory):
        os.mkdir(primary_data_directory)
    if not os.path.exists(primary_results_directory):
        os.mkdir(primary_results_directory)
    if not os.path.exists(secondary_data_directory):
        os.mkdir(secondary_data_directory)
    if not os.path.exists(secondary_results_directory):
        os.mkdir(secondary_results_directory)


if sys.version_info[0] < 3:
    sys.exit("This sample requires Python 3. Please install Python 3!")


time = 0
primary_result = []
primary_result_array = []
#print("Successful Setup")
tic = process_time()



# Loop to run consistently run on RasPi
while True:
    if sys_mode == 'test': # Testing on system
        triggered = 1
    if sys_mode == 'real': # Actual camera scenario
        triggered = mode_sentinel.main(camera, trigger, trigger_check, \
        trigger_sensitivity, args.rgb_res,image_burst, primary_type, primary_data_directory)
        #print("Event Detected")
    toc = process_time()
    draculae_timer = toc - tic
    if draculae_timer > draculae_freq:
        desmodus_draculae.main(primary_type, primary_data_directory, local_network, global_network)
        tic = process_time()
    if triggered == 1 :
        # Run Primary Model, which identifies/classifies species + confidence, and saves recorded and boxed images
        #print('Spinning up Primary Model', primary_model)
        #[primary_class, primary_confidence, primary_output_file] = ...
        primary_class, primary_confidence = mode_cnn.cnn(sys_mode, mcu, \
        primary_format, camera, args.rgb_res, \
        primary_type, args.pcnn_res, primary_model, primary_labels, \
        primary_data_directory, primary_results_directory, \
        current_background, args.sensitivity, max_images)
        #print('Model Complete')
        #print('Insert Code to Save Array in way that can be parsed for LoRa')
        #print('NOTE: CROPPED IMAGES AND .CSV RESULTS FILE ARE SAVED IN /DATA/RESULTS FOLDER ')

        # Run Secondary Model (if it exists)
        if secondary_model :
            #[secondary_class, secondary_confidence, secondary_output_file] = ...
            secondary_class, secondary_confidence = mode_cnn.main(sys_mode, mcu, \
            secondary_format, camera, args.rgb_res,\
            secondary_type, args.scnn_res, secondary_model_resolution, secondary_model, secondary_labels,\
            primary_results_directory, secondary_results_directory,
            current_background, args.sensitivity, max_images)
            print('Insert outcome from secondary model:')# secondary_class, secondary_confidence)
        # Run LoRa communication with outputs from primary algorithm
        if sys_mode == 'test':
            sys.exit('Completed Scenario')
        if sys_mode == 'real':
            triggered == 0
            print('System Reset')

    # Clear directory_list
    if clear_directories == 1:
        t_now = datetime.now().strftime("%Y%m%d_%H%M")

        primary_data_files = os.listdir(primary_data_directory)
        n_primary_data_folder = os.path.join(primary_data_directory,t_now)
        if not os.path.exists(n_primary_data_folder):
            os.mkdir(n_primary_data_folder)
        for f in primary_data_files :
            delete_path = os.path.join(primary_data_directory, f)
            shutil.move(delete_path,n_primary_data_folder)
            #os.remove(path)

        #primary_results_files = os.listdir(primary_results_directory)
        #n_primary_results_folder = os.path.join(primary_results_directory,t_now)
        #if not os.path.exists(n_primary_results_folder):
        #    os.mkdir(n_primary_results_folder)
        #for f in primary_results_files :
        #    path = os.path.join(primary_results_directory, f)
        #    shutil.move(path,n_primary_results_folder)
        if secondary_model != '':
            secondary_data_files = os.listdir(secondary_data_directory)
            n_secondary_data_folder = os.path.join(secondary_data_directory,t_now)
            if not os.path.exists(n_secondary_data_folder):
                os.mkdir(n_secondary_data_folder)
            for f in secondary_data_files :
                path = os.path.join(secondary_data_directory, f)
                shutil.move(path,n_secondary_data_folder)

    #if trigger_check == 0 and t_backgrond != 0 and time > t_backgrond :
    #    current_background = mode_background.main()
    #    t_background = 0
    #if trigger_check == 0 and t_lorawan != 0 and time > t_lorawan :
    if comms_type != '' and primary_confidence > ai_sensitivity:
        mode_comms.main(primary_class, primary_confidence, secondary_class, secondary_confidence, device_identifier, comms_type, comms_backend)
        t_lorawan = 0
    else :
        print('False Positive')
    print('Complete')

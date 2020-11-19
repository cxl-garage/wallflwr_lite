##### Tyto AI: Conservation X Labs   #####
## Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future

"""
This script processes data, and transforms the metadata into correct format for insight delivery
"""


import argparse
import time
import numpy as np
import os
from PIL import Image
import csv
import re
import datetime as dt
import sys
import shutil
import uuid
import edgetpu
from edgetpu.detection.engine import DetectionEngine
import cloud_data
import pandas as pd
from PIL import Image
from PIL import ImageChops
import logging

logger = logging.getLogger('cnn')


# Allows for localized training. Still in Development (CODE FROM GOOGLE UNDER APACHE 2.0)
def do_training(results,last_results,top_k):
    """Compares current model results to previous results and returns
    true if at least one label difference is detected. Used to collect
    images for training a custom model."""
    new_labels = [label[0] for label in results]
    old_labels = [label[0] for label in last_results]
    shared_labels  = set(new_labels).intersection(old_labels)
    if len(shared_labels) < top_k:
      print('Difference detected')
      return True

# Util function from Google
def load_labels(path):
  """Loads the labels file. Supports files with or without index numbers."""
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels

# Util function from Google
def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  #print('Interpreter:', interpreter)
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image

# Util function from Google
def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor



### Function to Save Cropped Images
def bb_crop(data_directory, file, aoi, result, classes, results_directory, insight_id,class_names):

    ## Checking that the directory exists, and creating it if it doesn't
    if not os.path.exists('{}'.format(data_directory)):
        os.makedirs('{}'.format(data_directory))

    # Setting a crop buffer so that additional context can be gained for those interested in slightly outside of bounded box
    crop_buffer = .15

    # open image
    file_path = os.path.join(data_directory,file)
    im = Image.open(file_path)

    # Make sure image is in RGB format
    if im.mode != 'RGB':
        im = im.convert('RGB')

    # save size of original (full-res) pic
    if not os.path.exists('../data/repo'):
        os.makedirs('../data/repo')
    filename = '../data/repo/{}'.format(file)
    im.save(filename)

    # make sure bounding boxes are within bounds of image
    for j in range(0,4) :
        if aoi[j] >= .50 :
            aoi[j] = aoi[j] + crop_buffer
        else :
            aoi[j] = aoi[j] - crop_buffer
        aoi[j] = max(min(aoi[j],1),0)

    # Convert bounded box coordinates from relative to absolute
    im_width, im_height = im.size
    left = int(aoi[0] * im_width)
    top = int(aoi[1] * im_height)
    right = int(aoi[2] * im_width)
    bottom = int(aoi[3] * im_height)

    # Saving image to file if the bounded box is sufficiently big
    if right-left > 15 and bottom -top > 15 :
        # this is all some funkiness to reshape everything to a pretty square without distorting (good for gui.py)
        height = bottom-top
        width =  right - left
                    #cropped_im = im.crop((left, top, right, bottom))
        if height < width:
            cropped_im = im.crop((left, (top+height/2)-(width/2), right, (top+height/2)+(width/2)))
        if width <= height:
            cropped_im = im.crop(((left+(width/2))-(height/2), top, (left+(width/2))+(height/2), bottom))
        cropped_im = cropped_im.resize((200,200))

        # Checking saving directory exists, and making it if necessary
        if not os.path.exists('{}/{}/'.format(results_directory,class_names[0][classes])):
            os.makedirs('{}/{}/'.format(results_directory,class_names[0][classes]))

        # Saving the cropped image
        filename = '{}/{}/{}.jpeg'.format(results_directory, class_names[0][classes],int(insight_id))
        cropped_im = cropped_im.save(filename)
    else :
        logger.error('ERROR: Bounded box is not large enough')



### Function to actually process images with Tensorflow Lite on the Coral
def tflite_im(alg,alg_df,format,interpreter, cnn_w, cnn_h, data_directory,file, threshold, results_directory,class_names):

    # Define the file to be processed
    file_path = os.path.join(data_directory,file)

    # Set up timer to check open time
    tic = time.process_time()

    # Initalize a dataframe to save metadata to
    meta_df = pd.DataFrame()


    try:
        # Attempt to open the image and resize it to correct size.
        current_file = Image.open(file_path).resize((cnn_h, cnn_w), Image.NEAREST)
        # Make sure image is in RGB format
        if current_file.mode != 'RGB':
            current_file = current_file.convert('RGB')

    # If file cannot be opened, it will be deleted from the SD card
    except Exception as e:
        logger.error('Issue opening {}'.format(file_path))
        delete_command = 'sudo rm -f {}'.format(file_path)
        os.system('echo {}|sudo -S {}'.format(os.environ.get('sudoPW'), delete_command))
        return meta_df
    toc = time.process_time()
    logger.info('Time to resize image: {} seconds'.format(toc - tic))


    # Set up timer to check processing time
    tic = time.process_time()

    # Run Tensorflow Lite on the Image
    ans = interpreter.DetectWithImage(current_file,threshold=threshold,keep_aspect_ratio =True, relative_coord=True,top_k=1)
    toc = time.process_time()
    logger.info('Time to run algorithm: {} seconds'.format(toc - tic))

    # Set up timer to check time to save images
    tic = time.process_time()

    # Intializing variables to process output of Tensoflow Engine
    i = 0
    meta = []
    thresh_classes = []
    thresh_scores = []
    count = ''

    # Assigning the local database unique ID (incremental)
    try:
        k = alg_df['insight_id'].iloc[-1] + 1
    except Exception as e:
        k = 1

    # If there was an insight that met the requirements, run this.
    if ans:

        # There may be multiple detections within one image, hence the for loop
        for obj in ans:

            boxes = obj.bounding_box.flatten()
            classes = obj.label_id
            scores = obj.score
            insight_id = int(k)
            # time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
            time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(os.path.getctime('{}'.format(file_path)))))

            logger.info('Class: {}'.format(class_names[0][classes]))
            logger.info('Confidence: {}'.format(scores))

            ## Processing outputs into the correct format for pandas DF
            meta = {'committed_sql':0,'committed_images':0,
            'committed_lora':0,'insight_id':insight_id,
            'alg_id':alg['alg_id'][0],'time_stamp': time_stamp,
            'class_id': classes,'class': class_names[0][classes],
            'confidence':scores,'image_id':file,'x_min':boxes[0],
            'y_min':boxes[1],'x_max':boxes[2],'y_max':boxes[3],
            'device_id':os.environ.get('device_id'),
            'device_name':os.environ.get('device_name')}

            # Appending data to pandas DF
            meta_df = meta_df.append(meta,ignore_index=True)

            # Running bb_crop to save original image and cropped image to file
            bb_crop(data_directory, file, boxes, meta, classes, results_directory, insight_id,class_names)

            k = k + 1

    ## If there was no class detected, we still want to save the image to the device for safe keeping
    else:

        # Checking that the "blank" directory has bee
        if not os.path.exists('{}/blank/'.format(results_directory)):
            os.makedirs('{}/blank/'.format(results_directory))

        # Define the path to the processed "blank" image
        file_path = os.path.join(data_directory,file)
        im = Image.open(file_path)

        # Save image to device
        filename = '{}/blank/{}.jpeg'.format(results_directory,file)
        im.save(filename)

        # Note: we still save the information about the image being processed, (negative data is still valuable) and thus it is still assigned an insight_id
        insight_id = int(k)
        # time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
        time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(os.path.getctime('{}'.format(file_path)))))
        meta = {'committed_sql':0,'committed_images':0,
        'committed_lora': 0,'insight_id':insight_id,'alg_id':alg['alg_id'][0],
        'time_stamp': time_stamp,'class_id':99,'class':'blank',
        'device_id':os.environ.get('device_id'),
        'device_name':os.environ.get('device_name'),'image_id':file}

        # Appending the "blank" image information to the local db (the csv)
        meta_df = meta_df.append(meta,ignore_index=True)


    toc = time.process_time()
    logger.info('Time to save images and metadata: {} seconds'.format(toc - tic))


    return meta_df




# The main function script
def main(alg,data_directory,quantize_type, algorithm_type = 'detection', batch = 10000, spacing = 10):
    
    
    # Defining the results directory
    results_directory   = '../data/results/{}'.format(alg['alg_id'][0])
    try:
    # Reading in the class names
        class_names = pd.read_csv('../models/{}.txt'.format(alg['alg_id'][0]), header=None)
    except Exception as e:
        logger.error('Unable to load model label {}'.format(alg['alg_id'][0]))

    # Checking if results directory exists, and if not, making it
    if not os.path.exists('{}'.format(results_directory)):
        os.makedirs('{}'.format(results_directory))

    # Defining the path to the model
    model = '../models/{}-{}.tflite'.format(alg['alg_id'][0],quantize_type)
    logger.info(model)

    # Defining the resolution of the images to be processed by the model
    cnn_w = int(alg['resolution'][0])
    cnn_h = int(alg['resolution'][0])

    # Defining the minimum confidence required
    ai_sensitivity = alg['sensitivity'][0]

    # Loading the model into tensorflow engine
    interpreter = DetectionEngine(model)

    x = 0
    directories = [str(data_directory),'../data/repo']
    while x < len(directories):
        # Finding all files within the data directory
        directory_list = os.listdir(directories[x])
        logger.info('Checking Directory: {}'.format(directories[x]))
        # Loading in the algorithm directory from file
        alg_df = pd.read_csv('../data/device_insights.csv')
        tempalg_df= alg_df
        ## Loop to understand the files potential relationship to other files (via time)
        k = 1
        spacing = [0]
        while k < len(directory_list):
            time1 = int(os.path.getctime('{}/{}'.format(directories[x],directory_list[k])))
            time2 = int(os.path.getctime('{}/{}'.format(directories[x],directory_list[k-1])))
            try:
                spacing.append(time1-time2)
            except Exception as e:
                spacing.append(999)
                logger.error('Failed to subtract the time')
            k = k + 1

        # initializing variables to enable grouping of files
        previous_confidence = 0
        previous_class = ''
        k = 0
        ## Looping through all files on the SD Card
        while k < len(directory_list):
            # Specifying the specific file to be processed
            file = directory_list[k]
            logger.info('File: {}'.format(file))

            # Checking that the file hasn't already been processed by this algorithm
            if ((alg_df['alg_id'] == alg['alg_id'][0]) & (alg_df['image_id'] == file)).any():
                logger.info('File already processed')
            else:
                # Checking if number of files checked has exceeded the "batch" variable (in production this should be inf)
                if k == batch:
                    logger.info('1')
                    break

                # Looping through files that is only broken if the spacing between files is above "spacing" variable seconds
                while 1:
                    # Defining a unique key for this group of insights
                    logger.info('2')
                        try:
                            group_key = alg_df['group_id'].iloc[-1] + 1
                        except Exception as e:
                            group_key = 1
                   

                    try:
                        # Break loop if the previous gap between files timestamp was greater than "spacing" variable
                        if spacing[k] > 10:
                            k = k + 1
                            logger.info('3')
                            break
                        if k > len(directory_list):
                            logger.info('4')
                            break
                        k = k + 1 
                    except Exception as e:
                        k = k + 1
                        logger.info('5')
                        break

                    ## Check that the file is actually a processable photo
                    #  Feature: Add ability to process videos
                    if file.endswith(".jpeg") or file.endswith(".JPG") or file.endswith(".jpg") or file.endswith(".JPEG") or file.endswith(".png") or file.endswith(".PNG"):
                            logger.info('6')
                            if algorithm_type == 'detection':
                                # Run the inference function, returns the bounded box metadata
                                meta_df = tflite_im(alg, alg_df, format, interpreter, cnn_w, cnn_h, directories[x], file, ai_sensitivity, results_directory,class_names)
                                logger.info('7')
                                # Appending the unique group key to the metadata
                                meta_df['group_id'] = group_key
                                logger.info(meta_df)
                                # Appending to existing results from the while loop
                                alg_df = alg_df.append(meta_df,ignore_index=True)
                                tempalg_df=alg_df
                                logger.info(alg_df)

                                # Adding group confidence from linked confidence between inferences
                                m = 0
                                while m < len(meta_df):
                                    # if the previous data inference within the same group had the same class, add the confidences.
                                    # note that this will only run if all detections within the current image are also the same as the previous image
                                    if previous_class == meta_df['class'][m]:
                                        try:
                                            previous_confidence = meta_df['confidence'][m] + previous_confidence
                                        except Exception as e:
                                            previous_confidence = previous_confidence
                                    previous_class = meta_df['class'][m]
                                    m = m+1
                            else:
                                logger.error('Type of algorithm not yet supported')
                    else:
                        break
                    # Adding the group confidence to any data point that has the same group key
                    alg_df.loc[alg_df['group_id'] == group_key,'group_confidence'] = previous_confidence
                    
            # Moving on to next file
            k = k + 1
        x = x + 1
    logger.info("11")
    logger.info(alg_df)
    logger.info(tempalg_df)
    # Making sure that only the correct columns are saved to file (due to created columns when merging dfs)
    alg_df = tempalg_df[['committed_sql','committed_images','committed_lora','insight_id','alg_id','time_stamp','class_id','class','confidence','image_id','x_min','y_min','x_max','y_max','device_id','group_id', 'group_confidence']]
    logger.info("12")
    logger.info(alg_df)
    # Saving insights to local DB (just a .csv for now)
    alg_df.to_csv('../data/device_insights.csv')
    logger.info("13")
    logger.info(alg_df)
    return alg_df


if __name__ == "__main__":
    main()
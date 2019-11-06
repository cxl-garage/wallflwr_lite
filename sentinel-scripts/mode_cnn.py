import argparse
import time
import numpy as np
import os
from PIL import Image
import csv
import re

from edgetpu.detection.engine import DetectionEngine
#from tflite_runtime.interpreter import Interpreter
if format == 'coral_acc':
    from edgetpu.detection.engine import DetectionEngine
    print('Loaded: Coral Accelerator')
    #from annotation import Annotator
if format == 'tflite' :
    from tflite_runtime.interpreter import Interpreter
    print('Loaded: tflite_runtime')
if format == 'tf_lite':
    from tensorflow.lite.python.interpreter import Interpreter
    print('Loaded: Tensorflow.Lite ')
if format == 'tensorflow' :
    import tensorflow as tf
    import keras
    from keras.models import load_model
    import math
    from pathlib import Path
    import numpy as np
    from PIL import Image
    from PIL.ExifTags import TAGS
    import cv2
    import pickle
    import requests
    print('Loaded: Tensorflow / Keras')
# Allows for localized training
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
# Annotate the identified objects
def live_annotate_objects(annotator, results, labels):
  """Draws the bounding box and label for each object in the results."""
  for obj in results:
    # Convert the bounding box figures from relative coordinates
    # to absolute coordinates based on the original resolution
    ymin, xmin, ymax, xmax = obj['bounding_box']
    xmin = int(xmin * CAMERA_WIDTH)
    xmax = int(xmax * CAMERA_WIDTH)
    ymin = int(ymin * CAMERA_HEIGHT)
    ymax = int(ymax * CAMERA_HEIGHT)

    # Overlay the box, label, and score on the camera preview
    annotator.bounding_box([xmin, ymin, xmax, ymax])
    annotator.text([xmin, ymin],
                   '%s\n%.2f' % (labels[obj['class_id']], obj['score']))
# Function to pull the labels from a path string
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

def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  #print('Interpreter:', interpreter)
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image

def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor
# Function to Save Cropped Images
def bb_crop(data_directory,file, aoi, result, classes, results_directory, i):
    crop_buffer = .15
    # open image
    file_path = os.path.join(data_directory,file)
    im = Image.open(file_path)
    # save size of original (full-res) pic
    im_width, im_height = im.size
    #print('Image Width', im_width)
    #print('Image Height', im_height)
    # make sure bounding boxes are within bounds of image
    for j in range(0,4) :
        if aoi[j] >= .50 :
            aoi[j] = aoi[j]+crop_buffer
        else :
            aoi[j] = aoi[j]-crop_buffer
        aoi[j] = max(min(aoi[j],1),0)
    #print('Area of Interest (fixed)',aoi)
    # pull coordinates and convert to correct of original (full-res) pic
    left = int(aoi[0] * im_width)
    right = int(aoi[2] * im_width)
    bottom = int(aoi[3] * im_height)
    top = int(aoi[1] * im_height)
    cropped_im = im.crop((left, top, right, bottom))
    filename = '%s/%s-%s' %(results_directory,str(i),file)
    #print('Saving Cropped Image as:',filename)
    cropped_im = cropped_im.save(filename)

def tflite_im(format,interpreter, input_width, input_height, data_directory,file, threshold, results_directory):
    """Returns a list of detection results, each a dictionary of object info."""
    file_path = os.path.join(data_directory,file)
    #print('Current Image:', file)
    current_file = Image.open(file_path).convert('RGB').resize(
      (input_height, input_width), Image.ANTIALIAS)
    tic = time.process_time()

    meta = []
    meta_array = []
    thresh_classes = []
    thresh_scores = []
    toc = time.process_time()
    clock = toc - tic
    count = ''

    if format == 'coral':
        #print('Coral Accelerator!')
        ans = interpreter.DetectWithImage(current_file,threshold=threshold,\
        keep_aspect_ratio =True, relative_coord=True,top_k=1)
        i = 0
        if ans:
            for obj in ans:
                boxes = obj.bounding_box
                classes = obj.label_id
                scores = obj.score
                count  = 1
                print('Need to add some code to allow multiple classes to be analyzed!')
                meta = {'file': file_path, 'bounding_box': boxes, 'class_ide': classes, 'score': scores, 'time': clock}
                thresh_classes = np.append(thresh_classes, classes)
                thresh_scores =np.append(thresh_scores, scores)
                #bb_crop(data_directory, file, boxes, meta, classes, results_directory, i)
                print('Add code for bounding box crop function (issue with the format)')
                meta_array = np.append(meta_array, meta)
                print(meta)
                i += 1

    else:
        # Get all output details
        boxes = get_output_tensor(interpreter, 0)
        classes = get_output_tensor(interpreter, 1)
        scores = get_output_tensor(interpreter, 2)
        count = int(get_output_tensor(interpreter, 3))
    #print(boxes[0,0])
    #if count:
        print('Boxes:',boxes)
        print('Classes',classes)
        print('Scores:',scores)
        for i in range(count):
            if scores[i] >= threshold or format == 'coral':
              # save results in an array
              meta = {
                  'file': file_path,
                  'bounding_box': boxes[i],
                  'class_id': classes[i],
                  'score': scores[i],
                  'time': clock}
              #print(boxes[i])
              thresh_classes = np.append(thresh_classes, classes[i])
              thresh_scores = np.append(thresh_scores, scores[i])
              bb_crop(data_directory, file, boxes[i], meta, classes[i], results_directory, i)
              meta_array = np.append(meta_array, meta)


    #print('Caution: Not returning all captured labels to confidence calcualtion')
    #print('Boxes Pulled from Numpy', meta['time'])
    return meta_array, thresh_classes, thresh_scores

# Defines the inputs to the script
def user_selections():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sys_mode', required=True,
                        help='Test or Real')
    parser.add_argument('--mcu', required=False, default='rpi0',
                        help='Type of Microcontroller')
    parser.add_argument('--vpu', required=False, default='rpi0',
                        help='Type of AI Processor')
    parser.add_argument('--model_format', required=True,
                        help='What format is the model in?')
    parser.add_argument('--model_type', required=True,
                        help='Image, Video, Acoustics, Motion')
    parser.add_argument('--model_file', required=True,
                        help='Specify the model file')
    parser.add_argument('--data_directory', required=True,
                        help='Where are the files being accessed')
    parser.add_argument('--results_directory', required=True,
                        help='Where are the files being saved')
    #parser.add_argument('--do_training', required=False, default = False,
    #                    help='Save relevant files for training custom model')
    parser.add_argument('--current_background', required=False, default='',
                        help='Last Recorded Background ')
    args = parser.parse_args()
    return args

# The main function script
def cnn(sys_mode, mcu, format, type, resolution, \
    model, labels, data_directory, results_directory, \
    current_background, ai_sensitivity, max_images):
    #import_model_type(format)
    import os
    directory = os.fsencode(data_directory)
    animal_detected = 0             # Initialize Animal Detector Counter (Confidence)
    detected_last_frame = False     # Initialize Detection Status
    bounding_boxes = []             #
    false_positive = 0              # Initialize False Positive Counter
    false_positive_threshold = 5    # How many frames to check before giving up
    image_burst = 10
    meta_array = []
    files_checked = 0
    confidence = []
    k = 1
    prev_class = 0
    prev_confidence = 0
    max_files = max_images
    classes = []
    cropped_image_counter = 1
    input_width = 100
    input_height = 100
    reset_results = 1

    print('Model Format:', format)
    print('Files being checked:', max_files)
    print("Labels File:",labels)

    # Sort out File Path
    if mcu == 'rpi0':
        model  = os.path.join('../', model)
        labels = os.path.join('../',labels)
        data_directory = os.path.join('../',data_directory)
        results_directory = os.path.join('../',results_directory)

    #if reset_results == 1:
    #    import os, shutil
    #    folder = results_directory
    #    for the_file in os.listdir(folder):
    #        file_path = os.path.join(folder, the_file)
    #        try:
    #            if os.path.isfile(file_path):
    #                os.unlink(file_path)
    #        #elif os.path.isdir(file_path): shutil.rmtree(file_path)
    #        except Exception as e:
    #            print(e)

    #print('Loaded CNN Parameters')

    if format == 'coral' :
        interpreter = DetectionEngine(model)
    else :
        labels = load_labels(labels)
        #print("Model File:",model)
        interpreter = Interpreter(model)
        print("interpreter variable:",interpreter)
        interpreter.allocate_tensors()
        _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']
        print('Image Input Size... Height', input_height,'Width:',input_width)

    if type == 'image' or 'acoustic':
        if sys_mode == 'real' :
            if mcu != rpi0 :
                sys.exit('Not ready for this part yet!')
            # take images directly from the camera buffer
            if confidence != 0 :
                # Reconstruct the input resolution to include color channel
                input_res = (resolution[0], resolution[1], 3)
                SINGLE_FRAME_SIZE_RGB = input_res[0] * input_res[1] * input_res[2]

                # Initialize the camera, set the resolution and framerate
                try:
                    camera = picamera.PiCamera()
                except picamera.exc.PiCameraMMALError:
                    print("\nPiCamera failed to open, do you have another task using it "
                          "in the background? Is your camera connected correctly?\n")
                    sys.exit("Connect your camera and kill other tasks using it to run "
                             "this sample.")

                # Initialize the buffer for picamera to hold the frame
                # https://picamera.readthedocs.io/en/release-1.13/api_streams.html?highlight=PiCameraCircularIO
                stream = picamera.PiCameraCircularIO(camera, size=SINGLE_FRAME_SIZE_RGB)
                # All essential camera settings
                camera.resolution = input_res[0:2]
                camera.framerate = args.camera_frame_rate
                camera.brightness = args.camera_brightness
                camera.shutter_speed = args.camera_shutter_speed
                camera.video_stabilization = args.camera_video_stablization

                # Get the frame from the CircularIO buffer.
                image = stream.getvalue()
                # The camera has not written anything to the CircularIO yet, thus no frame is been captured
                #if len(cam_buffer) != SINGLE_FRAME_SIZE_RGB:
                #    continue
                # Passing corresponding RGB
                results = tflite_im(interpreter, image, ai_sensitivity)
                #print(results)
                # If we already detected animal in this frame, we don't want to over count.
                if local_animal_detected and not detected_this_frame:
                    if animal_detected < args.detection_confidence:
                        # If we haven't confirmed, then increase our confidence.
                        if detected_last_frame:
                            animal_detected += 1
                        # If we didn't confirm last frame but we detected in this frame, we want to reset our confidence.
                        else:
                            animal_detected = 1
                # We detected an animal in this frame
                if local_animal_detected:
                    detected_this_frame = True
                    # Update the history
                    detected_last_frame = detected_this_frame
                    # Draw Bounding Box
                    bounding_boxes.append(result.rectangle)
                else:
                    print("Checking...")
                    false_positive += 1
                    save_data()
                if false_positive_threshold >= false_positive :
                    print("Cleaning up...")
                    camera.stop_recording()
                    camera.close()
            # take images from the initial burst triggered in mode_sentinel.py
            if confidence == 0 :
                for file in os.listdir(data_directory):
                    filename = os.fsdecode(file)
                    if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jpeg"):
                        current_image = os.path.join(data_directory,file)
                        #print('Current Image:', current_image)
                        results = tflite_im(interpreter, input_width, input_height, current_image, ai_sensitivity)
                    else:
                        print("All Burst Files Checked")
                        break

        # Test Scenario (running algorithm on files presaved to data_directory)
        if sys_mode == 'test' :
            print('Test Script Initialized...')
            for file in os.listdir(data_directory):
                if max_files < files_checked :
                    print('Checked all files')
                    break
                filename = os.fsdecode(file)
                if filename.endswith(".jpg") :
                    meta, n_classes, n_confidence = tflite_im(format, interpreter, input_width, input_height, \
                    data_directory,file, ai_sensitivity, results_directory)
                    #print(result)
                    meta_array = np.append(meta_array, meta)
                    classes = np.append(classes, n_classes)
                    confidence = np.append(confidence, n_confidence)
                    #print('Input to CNN:',image)
                else:
                    print("All files Checked")
                    break
                files_checked += 1


    if type == 'video' :
        print('Code for Video Recognition not Completed')

    # Write Results to timestamped .CSV File
    csv_file = '%s/_%s%s_%s%s%s.csv' %(results_directory,time.localtime()[1],time.localtime()[2],time.localtime()[3],time.localtime()[4],time.localtime()[5])
    csv_columns = ['file', 'bounding_box','class_id','score','time']
    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = csv_columns)
        writer.writeheader()
        for data in meta_array :
            writer.writerow(data)
    return classes, confidence


if __name__ == "__main__":
    main()

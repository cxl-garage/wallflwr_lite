
import argparse
import time
import numpy as np
import os
from PIL import Image
import csv
import re
import datetime as dt
import sys
import picamera
import shutil
from edgetpu.detection.engine import DetectionEngine
#print('Loaded: Coral Accelerator')


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
def bb_crop(data_directory, file, aoi, result, classes, results_directory, i):
    crop_buffer = .15
    # open image
    file_path = os.path.join(data_directory,file)
    im = Image.open(file_path)
    # save size of original (full-res) pic
    im_width, im_height = im.size
    # make sure bounding boxes are within bounds of image
    #print(aoi)
    for j in range(0,4) :
        #print(aoi[j])
        if aoi[j] >= .50 :
            aoi[j] = aoi[j] + crop_buffer
        else :
            aoi[j] = aoi[j] - crop_buffer
        aoi[j] = max(min(aoi[j],1),0)
        #print(aoi[j])
    #print('Area of Interest (fixed)',aoi)
    # pull coordinates and convert to correct of original (full-res) pic
    left = int(aoi[0] * im_width)
    top = int(aoi[1] * im_height)
    right = int(aoi[2] * im_width)
    bottom = int(aoi[3] * im_height)
    if right-left > 15 and bottom -top > 15 :
        #print('Image Width', im_width)
        #print('Image Height', im_height)
        #print(left,top,right,bottom)
        cropped_im = im.crop((left, top, right, bottom))
        filename = '%s/%s-%s' %(results_directory,str(i),file)
        #print('Saving Cropped Image as:',filename)
        cropped_im = cropped_im.save(filename)
    else :
        print('ERROR: Weird 0 pixel wide/tall bounding box')

def tflite_im(format,interpreter, cnn_w, cnn_h, data_directory,file, threshold, results_directory):
    """Returns a list of detection results, each a dictionary of object info."""
    file_path = os.path.join(data_directory,file)
    #print('Current Image:', file)
    current_file = Image.open(file_path).convert('RGB').resize(
      (cnn_h, cnn_w), Image.ANTIALIAS)
    tic = time.process_time()



    #print('Coral Accelerator!')
    ans = interpreter.DetectWithImage(current_file,threshold=threshold,\
    keep_aspect_ratio =True, relative_coord=True,top_k=1)

    toc = time.process_time()
    clock = toc - tic
    speed = 1/clock
    print('File Checked:', file)
    #print('Speed (Hz):',clock)

    i = 0
    meta = []
    meta_array = []
    thresh_classes = []
    thresh_scores = []
    count = ''
    if ans:
        for obj in ans:
            boxes = obj.bounding_box.flatten()
            #print(boxes)
            #print(type(boxes))
            classes = obj.label_id
            scores = obj.score
            count  = 1
            #print('Need to add some code to allow multiple classes to be analyzed!')
            meta = {'file': file_path, 'bounding_box': boxes, 'class_ide': classes, 'score': scores, 'time': clock}
            #meta = {file_path, boxes, classes, scores, clock}
            #print(meta)
            thresh_classes = np.append(thresh_classes, classes)
            thresh_scores =np.append(thresh_scores, scores)
            bb_crop(data_directory, file, boxes, meta, classes, results_directory, i)
            #print('Add code for bounding box crop function (issue with the format)')
            meta_array = np.append(meta_array, meta)
            #print(meta)
            i += 1

    return meta_array, thresh_classes, thresh_scores

# The main function script
def cnn(sys_mode, mcu, format, camera, im_resolution, \
    type, model_resolution, model, labels, data_directory, results_directory, \
    current_background, ai_sensitivity, max_images):
    directory_directory = os.fsencode(data_directory)
    animal_detected = 0             # Initialize Animal Detector Counter (Confidence)
    detected_last_frame = False     # Initialize Detection Status
    bounding_boxes = []             #
    false_positive = 0              # Initialize False Positive Counter
    false_positive_threshold = 5    # How many frames to check before giving up
    image_burst = 10
    meta_array = []
    files_checked = 0
    confidence = []
    sum_confidence = 0
    k = 1
    prev_class = 0
    prev_confidence = 0
    max_files = max_images
    classes = []
    cropped_image_counter = 1
    im_w  = int(im_resolution[0])
    im_h  = int(im_resolution[1])
    cnn_w = int(model_resolution[0])
    cnn_h = int(model_resolution[1])
    reset_results = 1

    #print('Model Format:', format)
    #print("Labels File:",labels)
    interpreter = DetectionEngine(model)


    directory_list = os.listdir(data_directory)
    while sum_confidence < 1 and files_checked < len(directory_list): #and max_files < files_checked:
        for file in directory_list:
            filename = os.fsdecode(file)
            path = os.path.join(data_directory,file)
            st = os.stat(path)
            mtime = dt.datetime.fromtimestamp(st.st_mtime)
            now = dt.datetime.now()
            ago = now-dt.timedelta(minutes=1)
            #print(mtime)
            #print(ago)
            if filename.endswith(".jpg"):# and mtime < ago:
                meta, n_classes, n_confidence = tflite_im(format, interpreter, \
                cnn_w, cnn_h, \
                data_directory,file, ai_sensitivity, results_directory)
                meta_array = np.append(meta_array, meta)
                classes = np.append(classes, n_classes)
                confidence = np.append(confidence, n_confidence)
                #print(n_confidence)
                sum_confidence = sum_confidence + sum(n_confidence)
                #print(sum_confidence)
            if sum_confidence > 1:
                break
            files_checked += 1
    if sys_mode == 'test' :
        print('Test Script Only, Camera Not Initialized...')
        return
    if sys_mode == 'real':
        if type == 'image' or 'acoustic':
            if mcu != 'rpi0' :
                sys.exit('Not ready for not RPi0 yet!')
            # take images directly from the camera buffer
            max_buffer_time = 0
            tic = 0
            while sum_confidence < 1 and max_buffer_time < 30:
                toc = time.process_time()
                max_buffer_time = max_buffer_time + (toc - tic)
                tic = time.process_time()
                print('Checked all burst files, failed to reach confidence, checking buffer...')
                if camera :
                    # Reconstruct the input resolution to include color channel
                    #input_res = (resolution[0], resolution[1], 3)
                    SINGLE_FRAME_SIZE_RGB = im_w * im_h #* 3

                    camera = picamera.PiCamera()
                    stream = picamera.PiCameraCircularIO(camera, size=SINGLE_FRAME_SIZE_RGB)
                    # All essential camera settings
                    camera.resolution = (im_w, im_h)
                    camera.framerate = 15
                    #camera.brightness = args.camera_brightness
                    #camera.shutter_speed = args.camera_shutter_speed
                    #camera.video_stabilization = args.camera_video_stablization

                    # Get the frame from the CircularIO buffer.
                    image = stream.getvalue()
                    # The camera has not written anything to the CircularIO yet, thus no frame is been captured
                    #if len(cam_buffer) != SINGLE_FRAME_SIZE_RGB:
                    #    continue
                    # Passing corresponding RGB
                    print(data_directory)
                    print(results_directory)
                    meta, n_classes, n_confidence = tflite_im(format, interpreter, cnn_w, cnn_h, \
                    data_directory,file, ai_sensitivity, results_directory)
                    #print(result)
                    meta_array = np.append(meta_array, meta)
                    classes = np.append(classes, n_classes)
                    confidence = np.append(confidence, n_confidence)
                    sum_confidence = sum_confidence + sum(n_confidence)
                else :
                    sys.exit('Need to have PiCamera, more camera functionality to come!')

                print("Cleaning up...")
                camera.close()

        if type == 'video' :
            print('Code for Video Recognition not Completed')

    # Write Results to timestamped .CSV File
    #csv_file = '%s/_%s%s_%s%s%s.csv' %(results_directory,time.localtime()[1],time.localtime()[2],time.localtime()[3],time.localtime()[4],time.localtime()[5])
    #csv_columns = ['file', 'bounding_box','class_id','score','time']
    #with open(csv_file, 'w') as csvfile:
    #    writer = csv.DictWriter(csvfile, fieldnames = csv_columns)
    #    writer.writeheader()
    #    for data in meta_array :
    #        writer.writerow(data)
    final_confidence = sum_confidence/files_checked*100
    final_class = n_classes*100

    return final_class, final_confidence


if __name__ == "__main__":
    main()

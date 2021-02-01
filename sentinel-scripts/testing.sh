#!/bin/bash
randomNumber=shuf -i 1-83 -n 1
echo $randomNumber
# sudo gsutil -m cp -r gs://sentinel_test_data/sentinel_squirrel_test_data/REDSQUIRREL ../data/camera/DCIM
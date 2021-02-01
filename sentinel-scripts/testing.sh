#!/bin/bash
ranNum=$[RANDOM%83+1]
echo $ranNum
"sudo gsutil -m cp -r gs://sentinel_test_data/sentinel_squirrel_test_data/REDSQUIRREL79 ../data/camera/DCIM"


# gs://sentinel_test_data/sentinel_squirrel_test_data/REDSQUIRREL$ranNum/ ../data/camera/DCIM"
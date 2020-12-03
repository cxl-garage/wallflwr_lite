#!/bin/bash

#This bash script runs the command to start the cloud proxy in the background. 

#The below four lines are there to log the outputs of this script
#Follow this: https://serverfault.com/questions/103501/how-can-i-fully-log-all-bash-scripts-actions
exec 3>&1 4>&2
trap 'exec 2>&4 1>&3' 0 1 2 3
exec 1>log.out 2>&1
echo “Started cloud proxy”


cd /
cd /home/pi/wallflwr_lite/sentinel-scripts
./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json -term_timeout=30s  & 




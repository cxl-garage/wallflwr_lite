#!/bin/bash
echo “Started bar.sh”
cd /
cd /home/pi/wallflwr_lite/sentinel-scripts
./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json 2>&1 >> log.txt & 





# command_1 2>&1 >> log.txt


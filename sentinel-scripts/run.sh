cd /
cd /home/pi/wallflwr_lite/sentinel-scripts
./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
# until grep -q "Ready for new connections"; do ; sleep 1; done; echo 'Found'
until grep -m 1 "Ready for new connections"; do ; sleep 1; done; echo 'Found'
python3 main.py

# sleep 5
# ./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
# sleep 5
# python3 main.py

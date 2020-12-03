cd /
cd /home/pi/wallflwr_lite/sentinel-scripts
./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
python3 main.py

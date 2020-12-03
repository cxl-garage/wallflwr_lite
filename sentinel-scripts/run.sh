cd /
cd /home/pi/wallflwr_lite/sentinel-scripts
./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
PID=$! #catch the last PID, here from command1
wait $PID #wait for command1, in background, to end
python3 main.py

# sleep 5
# ./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
# sleep 5
# python3 main.py

cd /
cd /home/pi/wallflwr_lite/sentinel-scripts
# # ./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
# # until grep -q "Ready for new connections"; do ; sleep 1; done; echo 'Found'
# # until grep -m 1 "Ready for new connections"; do ; sleep 1; done; echo 'Found'
# # ./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
# # sleep 1
# while ! grep -m1 'Ready for new connections' < ./log.out; do
#     sleep 1
#     echo Checking
# done
# echo Continue

# (./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json & &) | grep -q "Ready for new connections"

# python3 main.py

# sleep 5
# ./cloud_sql_proxy -instances=sentinel-project-278421:us-east4:algorithm-library=tcp:1234 -credential_file=../../credentials/sentinelDB.json &
# sleep 5
# python3 main.py


# FILE_TO_WATCH=./log.out
# SEARCH_PATTERN='Ready for new connections'

# tail -f -n0 ${FILE_TO_WATCH} | grep -qe ${SEARCH_PATTERN}

# if [ $? == 1 ]; then
#     echo "Search terminated without finding the pattern"
# fi

# python3 main.py


while ! grep -m1 'Ready for new connections' < ./log.out; do
    sleep 1
    echo HEYO
done

echo Continue
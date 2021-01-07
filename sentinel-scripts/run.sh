#!/bin/bash
cd /
cd /home/pi/wallflwr_lite/sentinel-scripts

#Make directory for logs
if [ ! -d /home/pi/wallflwr_lite/sentinel-scripts/logs ]; then
  mkdir -p /home/pi/wallflwr_lite/sentinel-scripts/logs;
fi

#Logs the whole process
exec 3>&1 4>&2
trap 'exec 2>&4 1>&3' 0 1 2 3
exec 1>logs/fullLog.out 2>&1


#Ping until we have internet (it will try for 30 seconds)
COUNTER=0
while [  $COUNTER -lt 3 ]; do
    ping -c 1 8.8.8.8 && break
    sleep 10
    let COUNTER=COUNTER+1 
done
echo $COUNTER

#If the device is connected to the internet, try to connect to the proxy
#You may ask why this is so logic heavy, it is becuase I hate bash and had to do this convoluted way for it to work
if [ $COUNTER -lt 3 ]
then
    #This will start the cloud proxy ONLY if there is internet
    bash cloud_proxy.sh

    #This while loop checks until the connection is made with the cloud SQL
    COUNTER2=0
    while [  $COUNTER2 -lt 10 ]; do
        if [ $COUNTER2 -eq 15 ]
        then
            echo SQL Timed Out
            break 
        else
            let COUNTER2=COUNTER2+1 
            sleep 2
            echo Connecting...
            
            # #This is just in case run.sh runs again with the proxy already running
            if grep -m1 'listen tcp 127.0.0.1:1234: bind: address already in use' < ./log.out;
            then
                echo SQL Already Connected
                let COUNTER2=99
                break
            fi

            #This is where the proxy connects
            if grep -m1 'Ready for new connections' < ./log.out;
            then
                echo SQL Connected
                let COUNTER2=99
                break
            fi

        fi
        
    done
fi

#Run the script 
#ENHANCEMENT: If it is connected to the internet, skip the same process found in the main.py 
python3 main.py 

#Uploading and shutting down
python3 upload_log.py

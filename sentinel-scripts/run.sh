cd /
cd /home/pi/wallflwr_lite/sentinel-scripts

#Ping until we have internet
while true; do    ping -c 1 8.8.8.8 && break; sleep 10; done
#This will start the cloud proxy
bash cloud_proxy.sh

#This while loop checks until the connection is made with the cloud SQL
while ! grep -m1 'Ready for new connections' < ./log.out; do
    sleep 2
    echo Connecting...
done

#Once connected it will run the main.py script
echo Connected to SQL
python3 main.py
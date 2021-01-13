#Ping until we have internet (it will try for 30 seconds)
COUNTER=0
INTERNET=0
while [  $COUNTER -lt 3 ]; do
    if ping -c 1 8.8.8.8 
    then
        echo Internet Connected
        let INTERNET=1 
        let COUNTER=99 
        break
    else
        sleep 10
        let COUNTER=COUNTER+1 
    fi
done



#If the device is connected to the internet, try to connect to the proxy
#You may ask why this is so logic heavy, it is becuase I hate bash and had to do this convoluted way for it to work
if [ $INTERNET=1 ]
then
    echo POOOP
fi


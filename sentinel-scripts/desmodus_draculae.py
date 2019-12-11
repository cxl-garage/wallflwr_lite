
import wifi
import os
from wireless import Wireless
wireless = Wireless()


def main(primary_type, data_directory, local_network, global_network):
    import time
    import_type = 0
    if primary_type == 'image':
        file_type = 'jpg'
    else:
        sys.exit("Draculae Functionality only available on images")
    print('Desmodus Draculae')

    data_directory = os.fsencode(data_directory)
    if local_network == 'sentinel_retrofit':
        PW_Local  = "WhalesRule!!"
    x = 0
    current_network = wireless.current()
    while current_network != local_network :
        wireless.connect(ssid=local_network,password=PW_Local)
        current_network = wireless.current()
        print('Waiting for Local Network Connection...')
        print(current_network)
        if x > 5:
            print("Connection Unsuccessful")
            break()
    if current_network == local_network
        print("Local Connection Successful")
        if import_type == 0:
            flashair_cmd = "sudo flashair-util -s -d ../data/rgb --only-jpg" #.format(str(data_directory), file_type)
        else:
            flashair_cmd = "sudo flashair-util -S -all -t 1999"
        print(flashair_cmd)
        os.system(flashair_cmd)
        print('Collecting Files from FlashAir')
    ## Disconnect from FlashAir WiFi
    if global_network == 'CXL':
        PW_Global  = "WhalesRule!!"
    current_network = wireless.current()
    while current_network != global_network:
        print('Waiting for Global Network Reconnection...')
        wireless.connect(ssid=global_network,password=PW_Global)
        current_network = wireless.current()
        print(current_network)
    print("Global Reconnection Successful")

    #Connect("CXL", "lemursrule")
    return

if __name__ == "__main__":
    main()

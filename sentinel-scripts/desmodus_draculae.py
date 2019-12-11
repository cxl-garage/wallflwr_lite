
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
    # Search WiFi and return WiFi list
    #h = Search()
    ## Connect to FlashAir
    h = wireless.current()
    print(h)
    if local_network == 'sentinel_retrofit':
        PW_Local  = "WhalesRule!!"
    wireless.connect(ssid=local_network,password=PW_Local)
    h = wireless.current()
    if h == local_network:
        print("Local Connection Successful")
    else:
        print("Connection Unsuccessful")
        ## Pull all relevant photos from SD clear directories
        time = 0
    if import_type == 0:
        flashair_cmd = "sudo flashair-util -s -d {} --only-{}".format(data_directory, file_type)
    else:
        flashair_cmd = "sudo flashair-util -S -all -t 1999"
    print(flashair_cmd)
    os.system(flashair_cmd)
    print('Collecting Files from FlashAir')
    ## Disconnect from FlashAir WiFi
    if global_network == 'CXL':
        PW_Global  = "WhalesRule!!"
    wireless.connect(ssid=global_network,password=PW_Global)
    h = wireless.current()
    while h != global_network:
        print('Waiting for Global Network Reconnection...')
        wireless.connect(ssid=global_network,password=PW_Global)
        h = wireless.current()
        time.sleep(1)
    print("Global Reconnection Successful")

    #Connect("CXL", "lemursrule")
    return

if __name__ == "__main__":
    main()


import wifi
import os
import time


# -*- coding: utf-8 -*-

import wifi


def Search():
    wifilist = []

    cells = wifi.Cell.all('wlan0')

    for cell in cells:
        wifilist.append(cell)

    return wifilist

def FindFromSearchList(ssid):
    wifilist = Search()

    for cell in wifilist:
        if cell.ssid == ssid:
            return cell

    return False

def FindFromSavedList(ssid):
    cell = wifi.Scheme.find('wlan0', ssid)

    if cell:
        return cell

    return False

def Connect(ssid, password=None):
    cell = FindFromSearchList(ssid)

    if cell:
        savedcell = FindFromSavedList(cell.ssid)

        # Already Saved from Setting
        if savedcell:
            savedcell.activate()
            return cell

        # First time to conenct
        else:
            if cell.encrypted:
                if password:
                    scheme = Add(cell, password)

                    try:
                        scheme.activate()

                    # Wrong Password
                    except wifi.exceptions.ConnectionError:
                        Delete(ssid)
                        return False

                    return cell
                else:
                    return False
            else:
                scheme = Add(cell)

                try:
                    scheme.activate()
                except wifi.exceptions.ConnectionError:
                    Delete(ssid)
                    return False

                return cell

    return False

def Add(cell, password=None):
    if not cell:
        return False

    scheme = wifi.Scheme.for_cell('wlan0', cell.ssid, cell, password)
    scheme.save()
    return scheme

def Delete(ssid):
    if not ssid:
        return False

    cell = FindFromSavedList(ssid)

    if cell:
        cell.delete()
        return True

    return False

def main(primary_type, data_directory):
    import_type = 1
    if primary_type == 'image':
        file_type = 'jpg'
    else:
        sys.exit("Draculae Functionality only available on images")
    print('Desmodus Draculae')

    data_directory = os.fsencode(data_directory)
    # Search WiFi and return WiFi list
    Search()
    print('Add functionality to check for existence of sentinel_retro')
    ## Connect to FlashAir
    SSID = "sentinel_retro"
    PW   = "WhalesRule!!"
    # Connect WiFi with password & without password
    #print Connect(SSID)
    connection_status = Connect(SSID, PW)
    print('Connecting...')
    time.sleep(10)
    if connection_status == 0:
        print("Sentinel Connection Unsuccessful")
    else:
        print("Sentinel Connection Successful")
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
        Search()
        Connect("CXL", "lemursrule")
    return

if __name__ == "__main__":
    main()

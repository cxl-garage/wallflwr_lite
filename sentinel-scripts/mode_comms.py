## Setup (Copy stable version into _master.py)
from __future__ import print_function
import argparse
import os
import shutil
import sys
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa



def main(primary_class, primary_confidence, secondary_class, secondary_confidence, device_identifier, comms_type, comms_backend):


	if comms_type == 'rfm9x'
		# Set Pin Outs
		i2c = busio.I2C(board.SCL, board.SDA)
		cs  = DigitalInOut(board.D27)
		rst = DigitalInOut(board.D22)
		irq = DigitalInOut(board.D23) #16
		en  = DigitalInOut(board.D17) #16
		spi=busio.SPI(board.SCK, MOSI= board.MOSI, MISO=board.MISO)
		rfm9x=adafruit_rfm9x.RFM9x(spi, cs, rst, 915.0)
		rfm9x.tx_power=23
		prev_packet=None

		# Initialize Communication to The Things Network
		if comms_backend == 'ttn'
			# ttn setup
			devaddr = bytearray([0x26, 0x02, 0x1B, 0xD9])
			nwkey = bytearray([0xF0, 0x23, 0x39, 0x26, 0xEC, 0x19, 0x1B, 0x77,
								0x8B, 0x23, 0xC8, 0x5D, 0x08, 0xA5, 0xDF, 0xDD])
			app = bytearray([0xDD, 0x91, 0x7C, 0x2B, 0x6F, 0xE7, 0xA0, 0x17, 0x32,
								0x5F, 0x50, 0x09, 0xE2, 0xBB, 0x4E, 0xBE])
			ttn_config = TTN(devaddr, nwkey, app, country='US')
			lora = TinyLoRa(spi, cs, irq, rst, ttn_config, channel=0)

		# Encode payload as bytes
		print('NOTE: Add Code to pull out correct data from the class/confidence vectors')
		data = bytearray(4)
	    data[0] = primary_class
	    data[1] = primary_confidence
	    data[2] = secondary_class
	    data[3] = secondary_confidence
		# Send Data
		lora.send_data(data, len(data), lora.frame_counter)
		print('Packet sent!')
		lora.frame_counter += 1
		return lora.frame_counter




if __name__ == '__main__':
    main()

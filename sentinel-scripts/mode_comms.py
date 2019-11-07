## Setup (Copy stable version into _master.py)
from __future__ import print_function
import argparse
import busio
import digitalio
import board
import os
import shutil
import sys
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa



def main(primary_class, primary_confidence, secondary_class, secondary_confidence, device_identifier, comms_type, comms_backend):


	if comms_type == 'lora_rfm9x':
		print('LoRa (rfm9x)')
		# Set Pin Outs
		i2c = busio.I2C(board.SCL, board.SDA)
		cs  = digitalio.DigitalInOut(board.D27)
		rst = digitalio.DigitalInOut(board.D22)
		irq = digitalio.DigitalInOut(board.D23) #16
		en  = digitalio.DigitalInOut(board.D17) #16
		#spi=busio.SPI(board.SCK, MOSI= board.MOSI, MISO=board.MISO)
		#rfm9x=adafruit_rfm9x.RFM9x(spi, cs, rst, 915.0)
		#rfm9x.tx_power=23
		#prev_packet=None

		# Initialize Communication to The Things Network
		if comms_backend == 'ttn':
			# TTN device address
			devaddr = bytearray([0x26, 0x02, 0x12, 0xD2])

			# TTN Network key
			nwkey = bytearray([0x4D, 0x79, 0x70, 0xE0, 0xED, 0xDC, 0x3C, 0xA1, 0xF7, 0x5F,
			0xE0, 0xF7, 0xD4, 0x15, 0x98, 0x8D])

			# TTN Application key
			app = bytearray([0x4F, 0x1B, 0xF2, 0x81, 0xCE, 0x85, 0xF1, 0xA8, 0xA6,
			0x48, 0x31, 0xBF, 0xBF, 0x61, 0xDA, 0x57])

			ttn_config = TTN(devaddr, nwkey, app, country='US')

			lora = TinyLoRa(spi, cs, irq, rst, ttn_config)

		data = [primary_class, primary_confidence, secondary_class, secondary_confidence]
		# Send Data
		print('Change logic to LoRa receipt confirmation (TTN downlink)')
		while lora.frame_counter < 10:
			print('Sending packet...')
			lora.send_data(data, len(data), lora.frame_counter)
			print(data)
			print('Packet sent!')
			lora.frame_counter += 1
			time.sleep(4)

		return




if __name__ == '__main__':
    main()

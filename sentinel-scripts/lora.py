##### Tyto AI: Conservation X Labs   #####
## Author: Sam Kelly

# This code is currently proprietary, further licensing will be decided in the near future

"""
This script is intended for LoRa communication of metadata from the Sentinel device to LoRa base stations
"""

from __future__ import print_function
import argparse
import busio
import digitalio
import board
import os
import shutil
import sys
import time
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa
import pandas as pd
import math
import numpy as np
import logging

logger = logging.getLogger('lora')

def main(attempts=1):
	try:
		insights = pd.read_csv('../data/device_insights.csv')
	except Exception as e:
		insights = pd.DataFrame(columns=['committed_sql','committed_images','committed_lora','insight_id','alg_id','time_stamp','class_id','class','confidence','image_id','x_min','y_min','x_max','y_max','device_id','group_id','group_confidence'])
	#device_info = pd.read_csv('../_device_info.csv')


	# Set Pin Outs
	i2c = busio.I2C(board.SCL, board.SDA)
	spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
	cs  = digitalio.DigitalInOut(board.D27)
	rst = digitalio.DigitalInOut(board.D22)
	irq = digitalio.DigitalInOut(board.D23) #16

	#devaddr = bytearray(device_info['lora_devaddr'][0],'utf-16')

	devaddr = bytearray([ 0x26, 0x02, 0x1E, 0x47 ])

	# TTN Network key
	#nwkey = bytearray(device_info['lora_nwkey'][0],'utf-16')

	nwkey = bytearray([ 0x40, 0x3A, 0xCC, 0x3B, 0xB3, 0xE2, 0x60, 0xF6, 0xC4, 0x6A, 0xC8, 0x22, 0x7C, 0xC5, 0xFD, 0xC3 ])

	# TTN Application key
	app = bytearray([ 0x23, 0xD4, 0x9D, 0x05, 0xE5, 0x1D, 0x32, 0xD8, 0xBB, 0xDF, 0x4B, 0xC8, 0x42, 0xEB, 0xF4, 0x20])

	ttn_config = TTN(devaddr, nwkey, app, country='US')

	lora = TinyLoRa(spi, cs, irq, rst, ttn_config)
	#print(insights)
	logger.info(len(insights))
	x =  insights[insights['committed_lora']!=True]
	logger.info(len(x))
	x = x[x['class'] != 'blank']
	logger.info(len(x))
	x = x[x['group_id'] != 'NaN']
	logger.info(len(x))
	x = x.drop_duplicates(subset=['group_id'], keep='last')
	x = x.reset_index()
	logger.info(x)
	k = 0
	if len(x) == 0:
		logger.info('Nothing to send over LoRa')
	while k < len(x):
		try:
			alg_id_1 = int(math.floor(x['alg_id'][k]/256))
			alg_id_2 = int(x['alg_id'][k])%256
			class_id = int(x['class_id'][k])
			confidence = int(x['group_confidence'][k]*50)
			local_insight_id_1 = int(math.floor(int(x['insight_id'][k])/256))
			local_insight_id_2 = int(x['insight_id'][k])%256
			data = [alg_id_1, alg_id_2, class_id, confidence, local_insight_id_1, local_insight_id_2]
			m = 0
			while m < attempts:
				#print('Sending packet...')
				lora.send_data(data, len(data), lora.frame_counter)
				logger.info(data)
				#lora.frame_counter += 1
				#time.sleep(5)
				m = m + 1
			time.sleep(0.5)
			insights.loc[insights['group_id'] == x['group_id'][k],'committed_lora'] = True
			insights.to_csv('../data/device_insights.csv')
			logger.info('LoRa Packet Sent!')
		except Exception as e:
			logger.error('Issue sending insight {}'.format(x['insight_id'][k]))
		k = k + 1

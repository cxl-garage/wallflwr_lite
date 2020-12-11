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
import adafruit_rfm69
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


	# Set Pin Outs
	i2c = busio.I2C(board.SCL, board.SDA)
	spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
	cs  = digitalio.DigitalInOut(board.D27)
	rst = digitalio.DigitalInOut(board.D22)
	irq = digitalio.DigitalInOut(board.D23) #16

	device_info = pd.read_csv('../_device_info.csv')
	devaddr = bytearray.fromhex(device_info['lora_devaddr'][0])#bytearray([ 0x26, 0x02, 0x1E, 0x47 ])
	nwkey = bytearray.fromhex(device_info['lora_nwkey'][0])
	app   = bytearray.fromhex(device_info['lora_appkey'][0])

	rfm69 = adafruit_rfm69.RFM69(spi, cs, rst, 915.0)
	rfm69.send('Hello world!')

	ttn_config = TTN(devaddr, nwkey, app, country='US')
	lora = TinyLoRa(spi, cs, irq, rst, ttn_config)
	print(insights)
	logger.info(len(insights))
	x =  insights[insights['committed_lora']!=True]
	x = x.drop_duplicates(subset=['group_id'], keep='first')
	x = x.reset_index()
	logger.info(x)
	k = 0
	if len(x) == 0:
		logger.info('Nothing to send over LoRa')
	while k < len(x):
		if x['group_confidence'] != 0:
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

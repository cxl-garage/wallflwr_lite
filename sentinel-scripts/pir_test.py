import RPi.GPIO as GPIO
import time

GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN)
while 1:
    pir_status = GPIO.input(4)
    if pir_status == 0:
         print('No Motion')
    if pir_status == 1:
       print('Motion Detected, awaiting confirmation')
    time.sleep(0.1)

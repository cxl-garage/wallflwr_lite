import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
<<<<<<< HEAD
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

=======
GPIO.setup(4, GPIO.IN)
>>>>>>> 60533a1bb3dd94243971ad3c80c18b1a4890df88
while 1:
    pir_status = GPIO.input(4)
    if pir_status == 0:
         print('No Motion')
    if pir_status == 1:
       print('Motion Detected, awaiting confirmation')
<<<<<<< HEAD
    time.sleep(0.5)
=======
    time.sleep(0.1)
>>>>>>> 60533a1bb3dd94243971ad3c80c18b1a4890df88

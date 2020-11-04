import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(19,GPIO.OUT)
GPIO.setup(26,GPIO.OUT)

#while 1:
GPIO.output(19,GPIO.HIGH)
GPIO.output(26,GPIO.HIGH)
time.sleep(0.5)
GPIO.cleanup()
time.sleep(0.5)


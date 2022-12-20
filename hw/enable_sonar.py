#!/usr/bin/env python3

# switch gpio 38 (gpio 77) high to enable sonar
# when the program exits, the gpio will be set low


import RPi.GPIO as GPIO
import atexit
import time


GPIO.setmode(GPIO.BOARD)
GPIO.setup(38, GPIO.OUT)
GPIO.output(38, GPIO.HIGH)


def exit_handler():
    print('My application is ending!')

atexit.register(exit_handler)   

# keep the program running
while True:
    try:
        time.sleep(1)
        print('Sonar is on')
    except KeyboardInterrupt:
        # clean up
        break


GPIO.output(38, GPIO.LOW)
GPIO.cleanup()

print('Sonar is off')

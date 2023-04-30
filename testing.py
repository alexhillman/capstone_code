#!/usr/bin/python

#
#     A script to control University of Arizona Capstone Project 23042 - Tabletop Silage Additive Research System
#           - manages I2C communication with Atlas Scientific's pH sensor, O2 sensor, Humidity/Temperature sensor
#           - manages SPI commmunication with MCP3008 ADC on channels 0/1 to communicate with MQ3 and MQ137 sensors
#           - manages GPIO pins to apply status LED (RGB)
#           - state machine implementing experimental data collection and upload to GitHub controlled via push button
#

# general import statements
import RPi.GPIO as GPIO
import io
import sys
import fcntl
import time
import datetime
import copy
import string
import smbus
import os
import requests
import base64

# Atlas Scientific I2C control library (included in same directory)
#from AtlasI2C import(AtlasI2C)

# state machine states
START = 1
STOP = 0

R = 1
G = 2
B = 3
LED_STATE = 1

# global variables and GPIO pins
RED = 17
GREEN = 27
BLUE = 22
BUTTON = 24



def button_callback(channel):
    global LED_STATE
    if(LED_STATE == R):
        LED_STATE = G
        GPIO.output(RED,   GPIO.LOW)
        GPIO.output(GREEN, GPIO.HIGH)
        GPIO.output(BLUE,  GPIO.LOW)
    elif(LED_STATE == G):
        LED_STATE = B
        GPIO.output(RED,   GPIO.LOW)
        GPIO.output(GREEN, GPIO.LOW)
        GPIO.output(BLUE,  GPIO.HIGH)
    elif(LED_STATE == B):
        LED_STATE = R
        GPIO.output(RED,   GPIO.HIGH)
        GPIO.output(GREEN, GPIO.LOW)
        GPIO.output(BLUE,  GPIO.LOW)

# main program loop
def main():
    global dataFile
    global numReads
    #########################################
    # INITIAL SETUP
    #########################################
    
    # initialize GPIO inputs and outputs
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # setup LEDs as outputs
    GPIO.setup(RED, GPIO.OUT)
    GPIO.setup(GREEN, GPIO.OUT)
    GPIO.setup(BLUE, GPIO.OUT)
    
    # set up push button as input with initial value to be pulled low (off)
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # set up the push button event as the falling edge of the voltage (releasing push button)
    GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_callback, bouncetime = 300)
    
    GPIO.output(RED,   GPIO.HIGH)
    GPIO.output(GREEN, GPIO.LOW)
    GPIO.output(BLUE,  GPIO.LOW)
    
    while True:
        time.sleep(0.1)
    
    GPIO.cleanup()

if __name__ == '__main__':
    main()

#!/usr/bin/python

#
#     A script to control University of Arizona Capstone Project 23042 - Tabletop Silage Additive Research System
#           - manages I2C communication with Atlas Scientific's pH sensor, O2 sensor, Humidity/Temperature sensor
#           - manages SPI commmunication with MCP3008 ADC on channels 0/1 to communicate with MQ3 and MQ137 sensors
#           - manages GPIO pins to apply status LED (RGB)
#           - state machine implementing experimental data collection and upload to GitHub controlled via push button
#

# general import statements
import gpiozero
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
from AtlasI2C import(AtlasI2C)

# state machine states
LED_STATE = "NONE"

def button_callback():
    global LED_STATE
    if(LED_STATE == "RED"):
        time.sleep(5)
    if(LED_STATE == "BLUE"):
        LED_STATE == "GREEN")
        
        
        

# main program loop
def main():
    global dataFile
    global numReads
    global pH_sensor
    global o2_sensor
    global humt_sensor
    global device_list
    
    #########################################
    # INITIAL SETUP
    #########################################
    
    # initialize GPIO inputs and outputs
    red   = LED(17) # GPIO17
    green = LED(27) # GPIO27
    blue  = LED(22) # GPIO22
    
    red.off()
    green.off()
    blue.off()
    
    button = Button(24) # GPIO24
    button.when_pressed = button_callback
    
    
    # Ping Each Sensor
    pH_sensor = AtlasI2C()
    o2_sensor = AtlasI2C()
    humt_sensor = AtlasI2C()
    
    # I2C
    device_list = get_devices()
    valid = [0, 0, 0]
    
    for device in device_list:
        if(device.address == 99): # pH sensor
            valid[0] = 1
            print("pH Sensor Connected")
        elif(device.address == 108):
            valid[1] = 1
            print("O2 Sensor Connected")
        elif(device.address == 111):
            valid[2] = 1
            print("Humidity/Temperature Sensor Connected")
    
    if(valid[0] + valid[1] + valid[2] != 3):
        LED_STATE = "RED"
        red.on()
    
    
    
    
    
    
    
    
    
    
    
    while True:
        time.sleep(0.1)
    
    GPIO.cleanup()

if __name__ == '__main__':
    main()

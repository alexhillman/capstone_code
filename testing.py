#!/usr/bin/python

#
#     A script to control University of Arizona Capstone Project 23042 - Tabletop Silage Additive Research System
#           - manages I2C communication with Atlas Scientific's pH sensor, O2 sensor, Humidity/Temperature sensor
#           - manages SPI commmunication with MCP3008 ADC on channels 0/1 to communicate with MQ3 and MQ137 sensors
#           - manages GPIO pins to apply status LED (RGB)
#           - state machine implementing experimental data collection and upload to GitHub controlled via push button
#

# general import statements
from gpiozero import Button
from gpiozero import LED
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
    elif(LED_STATE == "BLUE"):
        LED_STATE == "GREEN"
        blue.off()
        green.on()
    elif(LED_STATE == "GREEN"):
        LED_STATE == "BLUE"
        green.off()
        blue.on()
    elif(LED_STATE == "PURPLE"):
        LED_STATE == "BLUE"
        blue.off()
        red.off()
        green.on()
    
        
        
        

        
def get_devices():
    device = AtlasI2C()
    device_address_list = device.list_i2c_devices()
    device_list = []
    
    for i in device_address_list:
        device.set_i2c_address(i)
        response = device.query("I")
        try:
            moduletype = response.split(",")[1] 
            response = device.query("name,?").split(",")[1]
        except IndexError:
            #print(">> WARNING: device at I2C address " + str(i) + " has not been identified as an EZO device, and will not be queried") 
            continue
        device_list.append(AtlasI2C(address = i, moduletype = moduletype, name = response))
    return device_list 

# main program loop
def main():
    global dataFile
    global numReads
    global pH_sensor
    global o2_sensor
    global humt_sensor
    global device_list
    global red
    global blue
    global green
    
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
    
    
    ########################
    #   PING SENSORS
    ########################
    pH_sensor = AtlasI2C()
    o2_sensor = AtlasI2C()
    humt_sensor = AtlasI2C()
    
    # try to inialize the devices 5 times
    i = 0
    while i < 5:
        i += 1
        
        # I2C
        device_list = get_devices()
        valid = [0, 0, 0]
        
        # check all I2C devices
        for device in device_list:
            if(device.address == 99): # pH sensor
                valid[0] = 1
                pH_sensor = device
                print("pH Sensor Connected")
            elif(device.address == 108):
                valid[1] = 1
                o2_sensor = device
                print("O2 Sensor Connected")
            elif(device.address == 111):
                valid[2] = 1
                humt_sensor = device
                print("Humidity/Temperature Sensor Connected")
        
        # if all 3 sensors successful then stop looping
        if(valid[0] + valid[1] + valid[2] == 3):
            LED_STATE = "BLUE"
            blue.on()
            break
        else:
            print("Error finding Atlas Sensors. Trying Again\n")
    
    
    # if valid[] is still not 3, could not ping all 3 sensors
    if(valid[0] + valid[1] + valid[2] != 3): 
        LED_STATE = "RED"
        red.on()
    
   
    # can start an experiment
    while True:
        if(LED_STATE == "BLUE"):
            time.sleep(1)
        elif(LED_STATE == "GREEN" || LED_STATE == "PURPLE"):
    
    GPIO.cleanup()

if __name__ == '__main__':
    main()

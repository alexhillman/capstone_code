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
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
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
    print("you pushed the button in state " + LED_STATE)
    time.sleep(0.3)
    
    if(LED_STATE == "RED"):
        time.sleep(5)
    elif(LED_STATE == "BLUE"):
        LED_STATE = "GREEN"
    elif(LED_STATE == "GREEN"):
        LED_STATE = "BLUE"
    elif(LED_STATE == "PURPLE"):
        LED_STATE = "BLUE"
    
        
        
        

        
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
    global LED_STATE
    
    #########################################
    # INITIAL SETUP
    #########################################
    
    SPI_PORT = 0
    SPI_DEVICE = 0
    mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
    
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
    while i < 10:
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
            break
        else:
            print("Error finding Atlas Sensors. Trying Again\n")
    
    
    # if valid[] is still not 3, could not ping all 3 sensors
    if(valid[0] + valid[1] + valid[2] != 3): 
        LED_STATE = "RED"
        red.on()
    
   
    time_index=0
    time_interval = datetime.timedelta(seconds=30)   # HOW OFTEN TO READ DATA
    time_start = datetime.datetime.now()
    time_next = time_start + time_index * time_interval

    # can start an experiment
    while True:
        if(LED_STATE == "BLUE"):
            red.off()
            green.off()
            blue.on()
            time.sleep(0.1)
        elif(LED_STATE == "GREEN" or LED_STATE == "PURPLE"):
            if(LED_STATE == "GREEN"):
                red.off()
                green.on()
                blue.off()
            else:
                red.on()
                green.off()
                blue.on()
                time.sleep(0.1)
                
            # Read all Sensors
            time_now = datetime.datetime.now()
            if(time_now>=time_next):
                time_index = time_index+1
                time_next = time_start + time_index *time_interval
                
                # it's been 15 minutes: try conducting read until all successes
                valid = [0,0,0]
                pH = 0
                o2 = 0
                humidity = 0
                temperature = 0
                i = 0

                while(valid[0] + valid[1] + valid[2] != 3 and i < 10):
                    i += 1
                    valid = [0,0,0]
                    # read pH
                    pH_sensor.write("R")
                    time.sleep(pH_sensor.long_timeout)
                    pH_read = pH_sensor.read().split(' ')
                
                    if(pH_read[0] == "Success"):
                        pH = pH_read[4]
                        valid[0] = 1
                    
                    # read o2
                    o2_sensor.write("R")
                    time.sleep(o2_sensor.long_timeout)
                    o2_read = o2_sensor.read().split(' ')
                    
                    if(o2_read[0] == "Success"):
                        o2 = o2_read[4]
                        valid[1] = 1
                        
                    # read humidity and temp
                    humt_sensor.write("R")
                    time.sleep(humt_sensor.long_timeout)
                    humt_read = humt_sensor.read().split(' ')
                    
                    if(humt_read[0] == "Success"):
                        splitted = humt_read[4].split(',')
                        humidity = splitted[0]
                        temperature = splitted[1]
                        valid[2] = 1
                    
                    time.sleep(3)
                    
                # Could not get a valid reading
                if(i == 10):
                    LED_STATE = "PURPLE" # indicate to researcher minor error
                    pH = ''
                    o2 = ''
                    humidity = '' 
                    temperature = '' # remove data point
                
                # MQ accuracy is debatable after extensive humidity/high gas/temp testing - see Final Report for more.
                ethanol = int(abs((mcp.read_adc(0) - 475) * 1.4))
                ammonia = int(abs((mcp.read_adc(1) - 45) * 10))
                
                print("Read the following values:")
                print("pH: " + pH)
                print("o2: " + o2 + "%")
                print("humidity: " + humidity + "%")
                print("temp: " + temperature + " C")
                print("ethanol: " + str(ethanol) + " V")
                print("ammonia: " + str(ammonia) + " V")
                
                
            time.sleep(1)
            
            
    

if __name__ == '__main__':
    main()

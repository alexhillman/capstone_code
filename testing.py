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
import subprocess
import fcntl
import time
import datetime
import copy
import string
import smbus
import os
import requests
import base64
import pandas as pd
import matplotlib.pyplot as plt

# Atlas Scientific I2C control library (included in same directory)
from AtlasI2C import(AtlasI2C)

# state machine states
LED_STATE = "NONE"
experimentTime = 0
dataFile = 0
repoName = "/home/pi/Desktop/TSAR-main/"
credentialFile = "/home/pi/Desktop/scripts/access.txt"
dirName = 0
numReads = 0
githubToken = 0
githubAPIURL = 0

# github setup

def button_callback():
    global LED_STATE
    global experimentTime
    global dataFile
    global repoName
    global dirName
    
    print("you pushed the button in state " + LED_STATE + "\n")
    time.sleep(0.3)
    
    if(LED_STATE == "RED"):
        time.sleep(5)
    elif(LED_STATE == "BLUE"):
        # capture the time
        experimentTime = time.time()
        dirName = repoName + "experiments/experiment_" + time.strftime("%Y-%m-%d_%H-%M", time.gmtime(experimentTime)) + "/"
        os.mkdir(dirName)
        
        # create a new data file inside the new directory and generate column names
        dataFile = open(dirName+"data.csv", "w")
        dataFile.write("Time(s),Oxygen(%),pH,Humidity(%),Temperature(C),Ammonia(ppm),Ethanol(ppm)\n")
        dataFile.close()
        
        print("Starting Experiment @ "
              + datetime.datetime.fromtimestamp(experimentTime).strftime('%c')
              + "\n")
        
        LED_STATE = "GREEN"
        
    elif(LED_STATE == "GREEN" or LED_STATE == "PURPLE"):
        # PUSHING THE CSV DATA
        ###########################################################################################
        readFile = open(repoName +"README.md", "a")
        readFile.write(" ")
        readFile.close()


        subprocess.call("git add " + dirName + "/data.csv", shell = True)
        subprocess.call("git add " + "graph.png", shell = True)
        subprocess.call("git add " + "README.md", shell = True)
        subprocess.call("git config --global user.email \"tsar.23042@gmail.com\"", shell = True)
        subprocess.call("git config --global user.name \"TSAR CAPSTONE\"", shell = True)

        subprocess.call("git commit -m \"Data Upload\"", shell = True)
        subprocess.call("git push https://TSAR-23042-1:" + githubToken + "@github.com/TSAR-23042-1/TSAR-main.git", shell = True)
        ###########################################################################################
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
    global sensTime
    global dataFile
    global dirName
    global githubToken
    global githubAPIURL
    
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
    time_interval = datetime.timedelta(seconds=15)   # HOW OFTEN TO READ DATA
    time_start = datetime.datetime.now()
    time_next = time_start + time_index * time_interval

    f=open('/home/pi/Desktop/scripts/access.txt')
    lines=f.readlines()
    splitted = lines[1]
    githubToken = splitted.strip()

    
    ###################################################
    # can start an experiment
    ###################################################
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
                    
                    sensTime = time.time() - experimentTime
                    
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
                
                print("Read the following values:\n")
                print("pH: " + pH)
                print("o2: " + o2 + "%")
                print("humidity: " + humidity + "%")
                print("temp: " + temperature + " C")
                print("ethanol: " + str(ethanol) + " ppm")
                print("ammonia: " + str(ammonia) + " ppm")
                

                # write the read data to the data file
                if(i < 10):
                    dataFile = open(dirName+"data.csv", "a")
                    dataFile.write("{:.1f}, ".format(sensTime) + o2 + ", " + pH + ", " + humidity + ", " + temperature + ", " + str(ammonia) + ", " + str(ethanol) + "\n")
                    dataFile.close()
                
                
                
                    # update the plot
                    df = pd.read_csv(dirName + 'data.csv', header=0)
                    df=df.astype(float)

                    ax = df.plot(x='Time(s)', y=['Oxygen(%)', 'pH'], legend=None)
                    ax.set_ylabel("Concentration (% and pH)")
                    plt.title("Current TSAR Activity")
                    plt.savefig(repoName + 'graph.png')
                    plt.clf()
                    plt.close()
                
                
                numReads += 1
                if(numReads == 2):
                    numReads = 0
                    
                    readFile = open(repoName +"README.md", "a")
                    readFile.write(" ")
                    readFile.close()
                    
                    
                    subprocess.call("git add " + dirName + "/data.csv", shell = True)
                    subprocess.call("git add " + "graph.png", shell = True)
                    subprocess.call("git add " + "README.md", shell = True)
                    subprocess.call("git config --global user.email \"tsar.23042@gmail.com\"", shell = True)
                    subprocess.call("git config --global user.name \"TSAR CAPSTONE\"", shell = True)

                    subprocess.call("git commit -m \"Data Upload\"", shell = True)
                    subprocess.call("git push https://TSAR-23042-1:" + githubToken + "@github.com/TSAR-23042-1/TSAR-main.git", shell = True)
                    
                                 
            time.sleep(1)
            

if __name__ == '__main__':
    main()

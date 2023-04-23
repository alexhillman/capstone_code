#!/usr/bin/python

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

# also import the library for the Atlas Scientific produced I2C sensors
from AtlasI2C import(AtlasI2C)

# state machine states
START = 1
STOP = 0
    
# Global variables (GPIO pins and I2C addresses)
RED    = 22
GREEN  = 23
BLUE   = 24
BUTTON = 27
O2     = 0x6c
experimentTime = 0
dataFile = 0
dirName = "/home/pi/Desktop/experiments/23042prototype/"
numReads = 0






BTN_STATE = STOP # initial state of system is no experiment


def push_repo():
    githubAPIURL = "https://api.github.com/repos/fmalrs/23042prototype/contents/experiments/experiment_" + time.strftime("%Y-%m-%d_%H-%M", time.gmtime(experimentTime)) + "/data.csv"
    githubToken = "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"

    with open("/home/pi/Desktop/experiments/23042prototype/experiments/experiment_" + time.strftime("%Y-%m-%d_%H-%M", time.gmtime(experimentTime)) + "/data.csv", "rb") as f:
    # Encoding "my-local-image.jpg" to base64 format
    encodedData = base64.b64encode(f.read())

    headers = {
        "Authorization": f'''Bearer {githubToken}''',
        "Content-type": "application/vnd.github+json"
    }
    data = {
        "message": "My commit message", # Put your commit message here.
        "content": encodedData.decode("utf-8")
    }

    r = requests.put(githubAPIURL, headers=headers, json=data)
    

# print all EZO class devices in terminal (supplier provided function)
def print_devices(device_list, device):
    for i in device_list:
        if(i == device):
            print("--> " + i.get_device_info())
        else:
            print(" - " + i.get_device_info())
    #print("")

# check the I2C bus for compatible I2C Atlas devices (supplier provided function)
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
            print(">> WARNING: device at I2C address " + str(i) + " has not been identified as an EZO device, and will not be queried") 
            continue
        device_list.append(AtlasI2C(address = i, moduletype = moduletype, name = response))
    return device_list 



# push button event response function
def button_callback(channel):
    print("Button Pushed\n");
    global BTN_STATE
    global experimentTime
    global dirName
    global dataFile
    
    # flip the state of the button
    if(BTN_STATE == STOP):
        BTN_STATE = START
    else:
        BTN_STATE = STOP
    
    # act upon the current state
    if(BTN_STATE == STOP):
        print("Experiment Stopped, closing data file and pushing to GitHub...")
        
        GPIO.output(GREEN, GPIO.LOW)
        GPIO.output(RED,   GPIO.HIGH)
        
        # push the data file with whatever other data is present to Github
        repo.git.add("experiments/experiment_" + time.strftime("%Y-%m-%d_%H-%M", time.gmtime(experimentTime)) + "/data.csv")
        repo.index.commit("Experiment Concluded - Final data upload")
        origin = repo.remote(name="origin")
        origin.push()
        
        numReads = 0
        
        print("Github updated. Awaiting Next Experiment...")
    else:
        experimentTime = time.time()
        dirName = full_local_path + "experiments/experiment_" + time.strftime("%Y-%m-%d_%H-%M", time.gmtime(experimentTime)) + "/"
        os.mkdir(dirName)
        
        # create a new data file inside the new directory and generate column names
        dataFile = open(dirName+"data.csv", "w")
        dataFile.write("Oxygen (%), time (s),\n")
        dataFile.close()
        
        print("Starting Experiment @ "
              + datetime.datetime.fromtimestamp(experimentTime).strftime('%c')
              + "\n")
        GPIO.output(GREEN, GPIO.HIGH)
        GPIO.output(RED,   GPIO.LOW)
        GPIO.output(BLUE,  GPIO.LOW)
    
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
    GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_callback)

    # get the list of EZO devices and the first device in the list
    device_list = get_devices()
    device = device_list[0]
    real_raw_input = vars(__builtins__).get('raw_input', input)

    # initial state is STOP so light LEDs accordingly, do not read sensor/upload to git
    GPIO.output(GREEN, GPIO.LOW)
    GPIO.output(RED,   GPIO.HIGH)
    GPIO.output(BLUE,  GPIO.LOW)

    numReads = 0
    #########################################
    # POST-INITIALIZATION LOOPING
    #########################################
    while True:
        # only if an experiment is active
        if(BTN_STATE == START):
            # set read delay as the O2's required timeout
            delayTime = device.long_timeout
            
            GPIO.output(BLUE,  GPIO.HIGH)
            device.write("R")                    # issue read command
            time.sleep(delayTime)                # sleep for required time
            readSens = device.read().split(' ')  # read sensor value
            
            oxygen   = readSens[4]
            sensTime = time.time() - experimentTime
            
            print("O2: "+oxygen+"% at {:.2f} seconds post-start.".format(sensTime))
            
            # write the read data to the data file
            dataFile = open(dirName+"data.csv", "a")
            dataFile.write(oxygen + ", {:.2f},\n".format(sensTime))
            dataFile.close()
            
            numReads += 1
            GPIO.output(BLUE,  GPIO.LOW)
            time.sleep(3)
            
            # after 10 reads push data to github
            if((numReads >= 10) and (BTN_STATE == START)):
                repo.git.add("experiments/experiment_" + time.strftime("%Y-%m-%d_%H-%M", time.gmtime(experimentTime)) + "/data.csv")
                repo.index.commit("Uploading Data")
                origin = repo.remote(name="origin")
                origin.push()
                
                print("pushed to github\n")
                numReads = 0
            


    GPIO.cleanup()

if __name__ == '__main__':
    main()

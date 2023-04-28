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
from AtlasI2C import(AtlasI2C)

# state machine states
START = 1
STOP = 1

# 

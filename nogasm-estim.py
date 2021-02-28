#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Nogasm E-stim 2B controller, Connects Edge-o-Matic 3000 to E-Stim systems 2B
# Copyright (C) 2021 cb-stimmer

import serial
import sys
import time
import json
import asyncio
import websockets
import threading

settings = dict()
gVal = 0

def load_settings():
    with open("settings.json", "r") as read_file:
        global settings
        settings = json.load(read_file)


def send_command(serialport, command):
    command += '\r'
    command = command.encode()
    #print(command)
    #return
    ser = serial.Serial(serialport, 9600,timeout=10)  # open serial port
    ser.write(command)     # write a string
    reply = ser.readline()
    replyList = reply.split(b':')
    i = 0
    print(reply)
    #print('\n reply len = ')
    #print(len(replyList))
    while reply == 'ERR\r' or not ( len(replyList) == 9 or len(replyList) == 13 ):
	    ++i
	    time.sleep(1)
	    ser.write(command)
	    reply = ser.readline()
	    replyList = reply.split(b':')
	    print(reply)
	    if i ==10:
		    break
    ser.close()             # close port
    
def set_output(value):
    serialport = settings["serialPort"]
    minA = settings["levels"]["levelAmin"]
    maxA = settings["levels"]["levelAmax"]
    rangeA = maxA - minA
    minB = settings["levels"]["levelBmin"]
    maxB = settings["levels"]["levelBmax"]
    rangeB = maxB - minB
    maxMotor = settings["maxMotor"]
    valueA = minA + ((value * rangeA) / maxMotor)
    if value == 0:
        valueA = 0
    command = "A"
    command += str(round(valueA))
    send_command(serialport, command)
    valueB = minB + ((value * rangeB) / maxMotor)
    if value == 0:
        valueB = 0
    command = "B"
    command += str(round(valueB))
    send_command(serialport, command)
    
def init_estim():
    serialport = settings["serialPort"]
    mode = settings["mode"]
    power = settings["power"]
    send_command(serialport, power)
    command = "M"
    command += str(mode)
    send_command(serialport, command)
    command = "A0"
    send_command(serialport, command)
    command = "B0"
    send_command(serialport, command)


async def wsTread(treadName):
    global gVal
    async with websockets.connect(settings["nogasmURL"],ping_interval=None) as websocket:
        while 1:
            responce = await websocket.recv()
            responce = json.loads(responce)
            #print(responce)
            #print("tread ",treadName," Running")
            if 'readings' in responce.keys():
                gVal = responce['readings']['motor']
                #time.sleep(1)
        time.sleep(0.25)
 
def cmdTread(treadName):
    while 1:
        set_output(gVal)
        # print("tread ",treadName," Running")
        time.sleep(0.5)
    
load_settings()

init_estim()

#a = threading.Thread(target=wsTread, args=(1,))
b = threading.Thread(target=cmdTread, args=(2,))

#a.start()
b.start()

asyncio.get_event_loop().run_until_complete(wsTread("Main thing"))




#!/usr/bin/env python


import sys
import os
import math
import serial
import time

port = '/dev/ttyUSB1'
ser = serial.Serial(port, baudrate=2400, timeout = 10)

def get_serialAnswer(port):
	finished = 0;
	cmd_r=''
	while(finished == 0):
		cmd_r = cmd_r + port.read(port.inWaiting())
	
		if(cmd_r.find('\n') !=-1):
			finished = 1
		else:
			cmd_r = cmd_r +port.read(port.inWaiting())
		time.sleep(1)
	
	#parsed received answer
	cmd_r = cmd_r.split(' ')
	while '' in cmd_r:
		cmd_r.remove('')
	#print cmd_r
	return cmd_r

while(1):
	cmd_r = get_serialAnswer(ser)
	print 'message received: '
	print cmd_r
	cmd_r[2] = cmd_r[2].replace('\n',' ')
	cmd_s = "M "+ cmd_r[2] + str(cmd_r[1])+"\r"
	print cmd_s
	ser.write(cmd_s)
	time.sleep(0.1)

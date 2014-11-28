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

i = 0
while(1):
	cmd_r = get_serialAnswer(ser)
	print 'message received: ' + str(i)
	print cmd_r
	cmd_r[2] = cmd_r[2].replace('\n',' ')
	cmd_r[2]
	if cmd_r[2] == '5000 ':
		cmd_s = "T "+ cmd_r[2] + str(cmd_r[1])+"\r"
	else:
		cmd_s = "M "+ cmd_r[2] + str(cmd_r[1])+"\r"
	print cmd_s
	print "waiting antenna to move"
	i = i +1
	time.sleep(2)
	ser.write(cmd_s)
	print "answer sent"
	time.sleep(0.1)

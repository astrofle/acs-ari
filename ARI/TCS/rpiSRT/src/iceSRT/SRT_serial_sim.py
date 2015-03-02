#!/usr/bin/env python


import sys
import os
import math
import serial
import time
import random
import array
import struct
import threading

port = '/dev/ttyUSB1'
ser = serial.Serial(port, baudrate=2400, timeout = 10)

global msg
global calib

def get_serialAnswer(port):
	finished = 0;
	cmd_r=''
	while(finished == 0):
		print "waiting"
		cmd_r = cmd_r + port.read(port.inWaiting())
	
		if(cmd_r.find('\n') !=-1 or ('freq' in cmd_r and len(cmd_r)==9)):
			finished = 1
		else:
			cmd_r = cmd_r +port.read(port.inWaiting())
		time.sleep(1)
	
	#parsed received answer
	print cmd_r
	cmd_r = cmd_r.split(' ')
	while '' in cmd_r:
		cmd_r.remove('')
	#print cmd_r
	return cmd_r


def sim_antenna(cmd_r):
	global calib		
	if cmd_r[1] == '4':
		print "calout"
		sim_spectrum(graycorr, tsig = 0.0)
		calib = calib + 1
	if cmd_r[1] == '5':
		print "calin"
		sim_spectrum(graycorr, tsig = 300.0)
		calib = calib + 1
	if cmd_r[1] == '6':
		print "noise off"
		sim_spectrum(graycorr, tsig = 0.0)
		calib = calib + 1
	if cmd_r[1] == '7':
		print "noise on"
		sim_spectrum(graycorr, tsig = 200.0)
		calib = calib + 1
	cmd_r[2] = cmd_r[2].replace('\n',' ')
	cmd_r[2]
	if cmd_r[2] == '5000 ':
		cmd_s = "T "+ cmd_r[2] + str(cmd_r[1])+"\r"
	else:
		cmd_s = "M "+ cmd_r[2] + str(cmd_r[1])+"\r"
	print cmd_s
	print "waiting antenna to move"
	time.sleep(2)
	ser.write(cmd_s)
	print "answer sent"
	time.sleep(0.1)

def sim_spectrum(graycorr, tsig = 1000.0):
	global msg
	global spectrum
	spectrum = [0]*64
	tspill = 20.0
	print tsig
	#tsig = 1000 # Moon
	freqsep = 0.0078125
	intg = 0.52488
	print "creating spectrum"
	
	for i in range(64):
		power = 200.0 + tspill
		power += tsig
		power += power*gauss()/math.sqrt(freqsep*1e6*intg)
		power = power * graycorr[i]	
		if i<32:		
			spectrum[32+i] = int(power)
		else:
			spectrum[i-32] = int(power)	
	msg = array.array('H',spectrum).tostring()
	print max(spectrum)
	#Enviar datos por puerta serial
	return
			
def gauss():
	r = 0.0
	while(r>1.0 or r==0.0):
		v1 = 2.0 * random.random() - 1.0
		v2 = 2.0 * random.random() - 1.0
		r = v1 * v1 + v2 * v2
	fac = math.sqrt(-2.0 * math.log(r) / r)
	vv1 = v1 * fac
	return vv1

def sim_thread(graycorr):
	print "starting sim"
	sim_thread = threading.Thread(target = sim_spectrum, args=[graycorr], name = 'sim')
	sim_thread.start()
	return


print "starting SRT antenna and receiver simulator"

graycorr = [0]*64
cf = [1.000000, 1.006274, 1.022177, 1.040125, 1.051102, 1.048860, 1.033074, 1.009606,
0.987706, 0.975767, 0.977749, 0.991560, 1.009823, 1.022974, 1.023796, 1.011319,
0.991736, 0.975578, 0.972605, 0.986673, 1.012158, 1.032996, 1.025913, 0.968784,
0.851774, 0.684969, 0.496453, 0.320612, 0.183547, 0.094424, 0.046729, 0.026470,
0.021300]
	
	
for i in range(0,33):
	if (i < 32):
		graycorr[ i + 32]= cf[i];
	if (i < 33):
		graycorr[32 - i] = cf[i];

i = 0
calib = 0
sim_thread(graycorr)
#calib = 0 : genera un nuevo espectro para un comando freq
#calib = 1 :no cambia espectro cuando llegue freq	

while(1):
	if ser.inWaiting() > 0:
		print "calib ", calib
		cmd_r = get_serialAnswer(ser)
		print 'message received: ' + str(i)
		print cmd_r
		if 'freq' in cmd_r[0]:
			try:
				print "try"
				#print "calib", calib
				if calib==0:
					sim_thread(graycorr)				
				q = struct.unpack('b4s4b', cmd_r[0])
				print q
			except:
				print "command incomplete"
			print "sending spectrum"
			ser.write(msg)
			if calib == 2:
				calib = 0
		else:
			sim_antenna(cmd_r)	
		i = i + 1
		
	time.sleep(0.5)

import sys, traceback, Ice
sys.path.insert(0,'../clients/SRT_client/')

from time import sleep
import SRTClient
import SRTControlClient1 as SRTControl
import threading
import os
import socket


class SRTClientI(SRTClient.Client, SRTControl.SRT):
	def __init__(self):
		self.serialport = 'ttyUSB0'
		self.parameters = 'parametersV01'
		self.IP = 'default -h localhost -p 10010'
		self.antennaIP = '192.168.3.102 -p 10000'
	
	def setup(self, current = None):
		self.setIP(self.antennaIP)
		self.connect()
		self.SetSerialPort(self.serialport)
		self.Init(self.parameters)
		return "Antenna initialized and in stow position"
	
	def tracking(self, s, current = None):
		self.tracking(s)
		return "Tracking source"

#try:
#	if len(sys.argv)<2:
#		print "use SRTcontrolServer.py  -h 192.168.0.6 -p 10000"
#		sys.exit()
#	IP =  ' '.join(sys.argv[1:])
#	IP = "default -h " + IP
#except:
#	print "use SRTcontrolServer.py default -h 192.168.0.6 -p 10000 or 10001"
		
		
status = 0
ic = None
IP = 'default -h localhost -p 10010'

try:
	#ic = Ice.initialize(sys.argv)
	ic = Ice.initialize([''])
	#adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.6 -p 10000")
	adapter = ic.createObjectAdapterWithEndpoints("SRTClient", IP)
	object = SRTClientI()
	adapter.add(object, ic.stringToIdentity("SRTClient"))
	adapter.activate()
	print "SRT client up and running!"
	ic.waitForShutdown()
except:
	traceback.print_exc()
	status = 1

if ic:
	#clean up
	try:
		ic.destroy()
	except:
		traceback.print_exc()
		status = 1

sys.exit(status)

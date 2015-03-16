import sys, traceback, Ice
sys.path.insert(0,'../clients/SRT_client/')

from time import sleep
import SRTClient
import SRTControlClient1 as SRTControl
import threading
import os
import socket
import sites

class SRTClientI(SRTClient.Client, SRTControl.SRT):
	def __init__(self):
		self.serialport = 'ttyUSB0'
		self.parameters = 'parametersV01'
		self.IP = 'default -h localhost -p 10010'
		self.antennaIP = '192.168.3.101 -p 10000'
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars		
		print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		self.getspectrum = True
		self.spectra = 0
		self.portInUse = False
		self.spectrumStarted = False
		self.az = 0.0
		self.el = 0.0
		self.aznow = 0.0
		self.elnow = 0.0
		self.axis = 0
		self.tostow = 0
		self.elatstow = 0
		self.azatstow = 0
		self.slew = 0
		self.serialport = ''
		self.lastSRTCom = ''
		self.lastSerialMsg = ''
		self.IsMoving = False
		self.track = False
		self.OnSource = False
		self.target = None
		self.spectrum = []
	def setup(self, current = None):
		self.setIP(self.antennaIP)
		self.connect()
		self.SetSerialPort(self.serialport)
		print "sending antenna to Stow"
		self.Init(self.parameters)
		return "Antenna initialized and in stow position"
	
	def trackSource(self, s, current = None):
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

ARI_nodes = {'SRT1':{'client':'localhost -p 10010','antenna':'192.168.3.101 -p 10000'},
			'SRT2':{'client':'localhost -p 10011', 'antenna':'192.168.3.102 -p 10000'},
			'SH':'localhost -p 10012',
			'ROACH':'localhost -p 10013',
			}		
	
status = 0
ic = None

#IP = 'default -h localhost -p 10011'
IP = 'default -h '+ARI_nodes[sys.argv[1]]['client']


try:
	#ic = Ice.initialize(sys.argv)
	ic = Ice.initialize([''])
	#adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.6 -p 10000")
	adapter = ic.createObjectAdapterWithEndpoints("SRTClient", IP)
	object = SRTClientI()
	adapter.add(object, ic.stringToIdentity("SRTClient"))
	adapter.activate()
	print "SRT client up and running!"
	object.antennaIP = ARI_nodes[sys.argv[1]]['antenna']
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

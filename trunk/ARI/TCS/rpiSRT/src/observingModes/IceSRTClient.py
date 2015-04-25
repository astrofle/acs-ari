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
		self.IP = 'default -h localhost -p 10011'
		self.antennaIP = '192.168.3.102 -p 10000'
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars
		self.SRTsources = sites.SRTsources		
		print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		print str(len(self.SRTsources))+ " observable SRT sources: " + str(self.SRTsources.keys())
		self.getspectrum = True
		self.spectra = False
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
		self.lastSRTCom = ''
		self.lastSerialMsg = ''
		self.IsMoving = False
		self.track = False
		self.OnSource = False
		self.toSource = 0
		self.target = None
		self.spectrum = SRTClient.specs()
		self.initialized = False
		self.SRTinitialized = False
		self.name =''
		
	def setup(self, current = None):
		self.setIP(self.antennaIP)
		self.connect()
		sleep(0.5)
		print self.SRTinitialized
		if (not self.SRTinitialized):
			self.SetSerialPort(self.serialport)
			print self.name + " sending antenna to Stow"
			self.Init(self.parameters)
		else:
			self.initialized = True
		while(not self.initialized):
			sleep(1)
		return self.name + " Antenna initialized"
	
	def trackSource(self, s, current = None):
		self.tracking(s)
		while(not self.OnSource and (self.toSource != -1)):
			sleep(1)
		return self.name + " Antenna On Source and Tracking"
	
	def stopTrack(self, current = None):
		self.Stop()
		print self.name + " Stopping antenna and spectrum read"
		return self.name + " Track Stopped"

	def message(self, s, current = None):
		print s
		return s
		
	def getSpectrum(self, current = None):
		if not self.track:
			self.StartSpectrum()
		print self.name + " Getting new spectrum"
		while(self.spectra):
			sleep(0.5)
		print self.name + " New spectrum acquired"
		if not self.track:
			self.StopSpectrum()
		_sS = SRTClient.stamp(self.spectrum.sampleStamp.name, self.spectrum.sampleStamp.timdate, self.spectrum.sampleStamp.aznow, self.spectrum.sampleStamp.elnow, self.spectrum.sampleStamp.temperature, self.spectrum.sampleStamp.freq0, self.spectrum.sampleStamp.av, self.spectrum.sampleStamp.avc, self.spectrum.sampleStamp.nfreq, self.spectrum.sampleStamp.freqsep)
		_sp = SRTClient.specs(_sS , self.spectrum.specd, self.spectrum.spec, self.spectrum.avspec, self.spectrum.avspecc)
		return _sp

	def setFreq(self, freq, mode, current = None):
		self.SetFreq(freq, str(mode))
		print self.name +" setting receiver with freq " + str(freq) + " and mode " + str(mode)
		return self.name + " receiver set" 

	def stopSpectrum(self, current = None):
		self.StopSpectrum()
		return self.name + " Stopped spectrum reading"

#try:
#	if len(sys.argv)<2:
#		print "use SRTcontrolServer.py  -h 192.168.0.6 -p 10000"
#		sys.exit()
#	IP =  ' '.join(sys.argv[1:])
#	IP = "default -h " + IP
#except:
#	print "use SRTcontrolServer.py default -h 192.168.0.6 -p 10000 or 10001"

ARI_nodes = {'SRT1':{'client':'localhost -p 10011','antenna':'192.168.3.101 -p 10000'},
			'SRT2':{'client':'localhost -p 10012', 'antenna':'192.168.3.102 -p 10000'},
			'SH':'localhost -p 10013',
			'ROACH':'localhost -p 10014',
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

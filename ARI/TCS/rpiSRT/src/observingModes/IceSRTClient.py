import sys, traceback, Ice
sys.path.insert(0,'../clients/SRT_client/')

from time import sleep
import time
import SRTClient
import SRTControlClient1 as SRTControl
import threading
import os
import socket
import sites

class SRTClientI(SRTClient.Client, SRTControl.SRT):
	def __init__(self):
		self.Defaultserialport = 'ttyUSB0'
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
		self.spectrumStarted = False
		self.az = None
		self.el = None
		self.aznow = None
		self.elnow = None
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
		self.SRTinitialized = False #This variable check if SRT was initialised in a previous session
		self.name =''
		self.mode =''

		self.IP_string = "SRTController:default -h " + self.IP
		self.ic = None
		self.portInUse = [False, '']
		self.rGraph = True
		self.statusDisp = False
		self.RxSwitchMode = 'SD'
		########## 
		self.initialized = None
		self.slewing = False
		self.newAzEl = False
		self.cmdstop = False
		self.enSRT = True
		self.enSpec = True
		self.getStatus = True
		self.enObs = False
		self.SRTState = ''
		self.SRTMode = ''
		self.SRTTarget =''
		self.SRTonTarget = ''
		self.obsTarget = None
		self.SRTTrack = False
		self.azoffset = 0.0
		self.eloffset = 0.0
		self.azlim1 = None
		self.ellim1 = None
		self.azlim2 = None
		self.ellim2 = None
		self.azcmd = None
		self.elcmd = None
		self.Target = ''
		self.STOP = False
		self.map = []
		self.mapStarted = False
		print "Call shutdown before quiting ipython in order to kill all running threads, in a.o.c. exec ps and kill -9 in the console"
	
	def setup(self, current = None):
		print self.SRTinitialized
		if (not self.SRTinitialized):
			self.SetSerialPort(self.Defaultserialport)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) +" "+ self.name + " sending antenna to Stow"
			self.Init(self.parameters)
		else:
			self.initialized = True
		while(not self.initialized):
			sleep(1)
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) +" "+self.name + " Antenna initialized"
	
	def obsSRT(self, mode, target, current = None):
		if mode == 'GoTo':
			target = target.strip('[').strip(']').split(',')
			target[0] = float(target[0])
			target[1] = float(target[1])
		self.obswSRT(mode, target)
		#while(not self.SRTonTarget):
		#	sleep(1)
		#return self.name + " Antenna On Source and Tracking"
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) +" "+self.name + " Moving antenna to target"
	
	def StopObs(self, current = None):
		self.stopObs()
		print self.name + " Stopping antenna and spectrum read"
		return self.name + " Track Stopped"
		self.spectra = False
		self.slew = False
		return

	def message(self, s, current = None):
		print s
		return s
		
	def getSpectrum(self, current = None):
		#if not self.track:
		#	self.StartSpectrum()
		self.spectra = True
		print self.name + " Getting new spectrum"
		while(self.spectra or self.slew):
			print self.name + " waiting"
			print self.spectra
			print self.slew
			sleep(0.5)
		print self.name + " New spectrum acquired"
		#if not self.track:
		#	self.StopSpectrum()
		_sS = SRTClient.stamp(self.spectrum.sampleStamp.name, self.spectrum.sampleStamp.timdate, self.spectrum.sampleStamp.aznow, self.spectrum.sampleStamp.elnow, self.spectrum.sampleStamp.temperature, self.spectrum.sampleStamp.freq0, self.spectrum.sampleStamp.av, self.spectrum.sampleStamp.avc, self.spectrum.sampleStamp.nfreq, self.spectrum.sampleStamp.freqsep)
		_sp = SRTClient.specs(_sS , self.spectrum.specd, self.spectrum.spec, self.spectrum.avspec, self.spectrum.avspecc)
		return _sp

	def setFreq(self, freq, mode, current = None):
		self.SetFreq(freq, str(mode))
		print self.name +" setting receiver with freq " + str(freq) + " and mode " + str(mode)
		return self.name + " receiver set" 

	def stopSpectrum(self, current = None):
		self.disableSpectrum()
		sleep(10)
		self.spectra = False
		return self.name + " Stopped spectrum reading"

	def startSpectrum(self, current = None):
		self.enableSpectrum()
		return self.name + " Stopped spectrum reading"
		
	def setRxMode(self, mode, current = None):
	    print "setting " + self.name + "to " + mode + "mode"
	    self.mode = mode
	    self.SetRxMode(mode)
	    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) +" "+self.name + " set for " + self.mode
	    
	def SRTstate(self, current = None):
		_st = SRTClient.state(str(self.name),time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),str(self.SRTState),str(self.SRTonTarget), str(self.SRTMode),\
		str(self.SRTTarget),str(self.SRTTrack),str(self.enObs),str(self.newAzEl),\
		str(self.enSRT), str(self.enSpec),str(self.slewing),str(self.cmdstop),\
		str(self.IsMoving),str(self.getStatus),str(self.portInUse),str(self.spectra),\
		str(self.RxSwitchMode),str(self.toSource),str(self.SRTinitialized),\
		str(self.initialized),str(self.tostow),str(self.Target),str(self.obsTarget),\
		str(self.az),str(self.el),str(self.aznow),str(self.elnow),str(self.azoffset), str(self.eloffset),str(self.axis),\
		str(self.tostow),str(self.elatstow),str(self.azatstow),str(self.slew),\
		str(self.serialport),str(self.lastSRTCom),str(self.lastSerialMsg ))
		return _st

	def offsetPointing(self, azoff, eloff, current = None):
		print "setting offset to az:" + str(azoff)+" el:"+str(eloff)
		self.setOffsetPointing(azoff, eloff)
		return self.name +  "offset set to az:" + str(azoff)+" el:"+str(eloff)
		
	def NpointScan(self, points, delta, sp, current = None):
		print "starting n-point map"
		if sp == 'True':
			sp = True
		print sp
		self.npointScan(points, delta, sp)
		return []
	
	def SRTStow(self, current = None):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + self.name + " sending antenna to Stow"
		self.Stow()
		sleep(1)
		print self.portInUse[0]
		while(self.portInUse[0]):
			sleep(1)
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) +" "+self.name + " Antenna Stowed"
		
	def SRTStopGoingToTarget(self, current = None):
		self.stopGoingToTarget()
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) +" "+self.name + " Stopping antenna"
		
	def ClientThreads(self, current = None):
		th = threading.enumerate()
		print th
		return self.name + " client threads"


		
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
	object.setIP(object.antennaIP)
	object.connect()
	sleep(0.5)
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

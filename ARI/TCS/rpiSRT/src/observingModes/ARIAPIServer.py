import sys, traceback, Ice

sys.path.append('../IceClients/')
import SRTClient
import SHControl
from time import sleep
import ARIAPI
import obsmodeV04 as ARIobsMode
import threading
import os
import socket
import sites
import time

class ARIAPII(ARIAPI.API):
	def __init__(self):
		self.ARI_nodes = {
		'SRT1':"SRTClient:default -h localhost -p 10011",
		'SRT2':"SRTClient:default -h localhost -p 10012",
		'SH':"SHController:default -h localhost -p 10013",
		'ROACH':"SRTClient:default -h localhost -p 10014"
		}
		self.ics = {}
		self.observingMode = ""
		self.antenna = ''
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars
		self.SRTsources = sites.SRTsources
		self.radecSources = []
		#print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		#print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		#print str(len(self.SRTsources))+ " observable SRT sources: " + str(self.SRTsources.keys())	

		self.radio_config = False
		self.freq = 1420.4
		self.rec_mode = '1'
		self.new_freq = 1420.4
		self.new_rec_mode = '1'
		self.Target = ""
		self.spec = SRTClient.specs()
		self.spectrum ={}
		self.SHspectrum = SHControl.SHspectrum()
		self.observe = False
		self.getSHsp = False
		#######
		self.readSpectrum = False
		self.rcvSpec = [0,0]
		
		self.OnSrc =[0,0]
		self.lastSpd =[0,0]
		self.status =[]
		self.waitSpectrum = False
		self.stowInProgress = False
		#######
		self.setupInProgress = False
		self.initialized = {
		'SRT1':False,
		'SRT2':False,
		'SH':False,
		'ROACH':False}
		self.atStow = {
		'SRT1':False,
		'SRT2':False}
		self.RxSwmode = {
		'SRT1':'',
		'SRT2':''}
		self.RxSetup = {
		'SRT1':[],
		'SRT2':[]
		}
		self.ArrayOnTarget = {
		'SRT1':False,
		'SRT2':False
		}
		self.NewSpectrum ={
		'SRT1':False,
		'SRT2':False
		}
		self.ArrayMovingToTarget = False
		self.ArrayStopCmd = False
		self.Clientstatus ={}
		self.getClStatus = True
		self.offsets = [0,0]
		self.map =None
		self.scanMapInProgress = False
		self.readSpectrum
		####

	def testConn(self, s, current = None):
		print s
		return s


	def setObservingMode(self, s1, s2, current = None):
		if (s1 == "SD"):
			if (s2 == "Double"):
				self.obsMode = ARIobsMode.SRTDoubleSingleDish()
				msg = "Double Single Dish Mode chosen"
			else:
				self.obsMode = ARIobsModee.SRTSingleDish(s2)
				msg = "Single Dish Mode chosen with " + s2
		elif (s1 == "ARI"):
			if (s2 == "SH"):
				self.obsMode = ARIobsMode.ARI_SignalHound()
				msg = "ARI Signal Hound Mode chosen"
			elif (s2 == "ROACH"):
				self.obsMode = ARIobsMode.ARI_ROACH()
				msg = "ARI ROACH Mode chosen"
		else:
			msg = "error in parameters"	
		print msg
		return msg
		
	def createObservingMode(self, current = None):
		self.obsMode.createObsMode()
		msg = "Observing Mode Created"
		print msg
		return msg
	
	def setupArray(self, current = None):
		self.obsMode.setup()
		msg = "Initializing array"
		print msg
		return msg
	
	def observeWithArray(self, mode, target, current = None):
		if mode == 'GoTo':
			target = target.strip('[').strip(']').split(',')
			target[0] = float(target[0])
			target[1] = float(target[1])
		self.obsMode.obswArray(mode, target)
		msg = "Commanding array"
	
	def setRxArray(self, freq, RxMode, current = None):
		self.obsMode.radioSetup(freq, RxMode)
		msg = "Receiver and Target Set"
		print msg
		return msg
		
	def setARISH(self, _fc, _bw, current = None):
		fc = _fc*1e6
		bw = _bw*1e6
		self.obsMode.SH_setBW(bw)
		while(not self.obsMode.SH_bwSetup):
			time.sleep(0.5)
		self.obsMode.SH_setfc(fc)
		while(not self.obsMode.SH_fcSetup):
			time.sleep(0.5)
		
	def setRxSwMode(self, node, RxSwMode, current = None):
		self.obsmode.SwRxMode(self, node, mode)
		msg = "Receiver Switch Mode Set"
		print msg
		return msg
	
	def enableSpectrumArray(self, current = None):
		self.obsMode.enableSpectrum()
		msg = "Getting Spectrum from SRT Rx"
		print msg
		return msg

	def disableSpectrumArray(self, current = None):
		self.obsMode.disableSpectrum()
		msg = "Stopping spectrum from SRT Rx"
		print msg
		return msg
		
	def npointScanMap(self, points, delta, spec, current = None):
		if spec == 'True':
			specB = True
		else:
			specB = False
		print spec
		self.obsMode.npointScanMap(points, delta, specB)
		msg = "Executing n-points Scan Map"
		print msg
		return self.map
	
	def findRaDecSources(self, current = None):
		sources = []
		self.obsMode.find_radec(False)
		for i in self.obsMode.radecSources:
			azel = self.obsMode.radecSources[i]['azel']
			azels = ARIAPI.astro(i, azel[0], azel[1])
			sources.append(azels)
		print sources
		return sources

	def findPlanets(self, current = None):
		sources = []
		self.obsMode.find_planets(False)
		for i in self.obsMode.planets:
			azel = self.obsMode.planets[i]['azel']
			azels = ARIAPI.astro(i, azel[0], azel[1])
			sources.append(azels)
		return sources

	def findStars(self, current = None):
		sources = []
		self.obsMode.find_stars(False)
		for i in self.obsMode.stars:
			azel = self.obsMode.stars[i]['azel']
			azels = ARIAPI.astro(i, azel[0], azel[1])
			sources.append(azels)
		return sources

	def clientShutdown(self, current = None):
		self.obsMode.ClientShutdown()
		msg = "Shutdown Client"
		return msg

	def obsModeShutdown(self, current = None):
		self.obsMode.shutdown()
		msg = "Shutdown Observing Mode Server"
		return msg

	def stowArray(self, current = None):
		self.obsMode.Stow()
		msg = "Stow Array"
		return msg

	def stopArray(self, current = None):
		self.obsMode.stopArray()
		msg = "Stopping Array"
		return msg

	def stopGoingToTarget(self, current = None):
		self.obsMode.stopGoingtoTarget()
		msg = "Stopping Array to Target"
		return msg

	def setOffsetPointing(self, azoff, eloff, current = None):
		self.obsMode.SetOffsetPointing(azoff, eloff)
		msg = "Setting offset"
		return msg

	def getObsModeState(self, current = None):
		self.obsMode.states()
		msg = "Getting observing mode state"
		st = ARIAPI.OMstate(self.obsMode.observingMode, self.obsMode.nodes,\
		self.obsMode.ARI_controllersTXT, self.obsMode.setupInProgress,\
		self.obsMode.initialized, self.obsMode.atStow, self.obsMode.stowInProgress,\
		self.obsMode.mode, self.obsMode.RxSwmode, self.obsMode.RxSetup,\
		self.obsMode.new_freq, self.obsMode.new_rec_mode, self.obsMode.getClStatus,\
		self.obsMode.ArrayMovingToTarget, self.obsMode.ArrayOnTarget,\
		self.obsMode.ArrayStopCmd, self.obsMode.offsets, self.obsMode.scanMapInProgress,\
		self.obsMode.readSpectrum, self.obsMode.NewSpectrum, self.obsMode.waitSpectrum)
		return st

	def getArrayState(self, current = None):
		msg = "Getting array state"
		_st = {}
		for node in self.obsMode.nodes:
			if node.starswith('SRT'):
				_piu = ARIAPI.piu(self.obsMode.Clientstatus[node].portInUse.InUse,\
				self.obsMode.Clientstatus[node].portInUse.Routine)
				_sts = ARIAPI.ClState(self.obsMode.Clientstatus[node].name,\
				self.obsMode.Clientstatus[node].time,\
				self.obsMode.Clientstatus[node].SRTState,\
				self.obsMode.Clientstatus[node].SRTonTarget,\
				self.obsMode.Clientstatus[node].SRTMode,\
				self.obsMode.Clientstatus[node].SRTTarget,\
				self.obsMode.Clientstatus[node].SRTTrack,\
				self.obsMode.Clientstatus[node].enObs,\
				self.obsMode.Clientstatus[node].newAzEl,\
				self.obsMode.Clientstatus[node].enSRT,\
				self.obsMode.Clientstatus[node].enSpec,\
				self.obsMode.Clientstatus[node].slewing,\
				self.obsMode.Clientstatus[node].cmdstop,\
				self.obsMode.Clientstatus[node].IsMoving,\
				self.obsMode.Clientstatus[node].getStatus,\
				_piu,\
				self.obsMode.Clientstatus[node].spectra,\
				self.obsMode.Clientstatus[node].RxSwitchMode,\
				self.obsMode.Clientstatus[node].toSource,\
				self.obsMode.Clientstatus[node].SRTinitialized,\
				self.obsMode.Clientstatus[node].initialized,\
				self.obsMode.Clientstatus[node].Target,\
				self.obsMode.Clientstatus[node].obsTarget,\
				self.obsMode.Clientstatus[node].az,\
				self.obsMode.Clientstatus[node].el,\
				self.obsMode.Clientstatus[node].aznow,\
				self.obsMode.Clientstatus[node].elnow,\
				self.obsMode.Clientstatus[node].azoffset,\
				self.obsMode.Clientstatus[node].eloffset,\
				self.obsMode.Clientstatus[node].axis,\
				self.obsMode.Clientstatus[node].tostow,\
				self.obsMode.Clientstatus[node].elatstow,\
				self.obsMode.Clientstatus[node].azatstow,\
				self.obsMode.Clientstatus[node].slew,\
				self.obsMode.Clientstatus[node].serialport,\
				self.obsMode.Clientstatus[node].lastSRTCom,\
				self.obsMode.Clientstatus[node].lastSerialMsg)
				_st[node] = _sts
		return _st
		
	def getLastSpectrum(self, current = None):
		lastSpectrum = {}
		for node in self.obsMode.nodes:
			_sp = self.obsMode.spectrum[node]
			print _sp.sampleStamp.name
			_stamp =ARIAPI.stamp(_sp.sampleStamp.name,\
			_sp.sampleStamp.timdate,_sp.sampleStamp.aznow,\
			_sp.sampleStamp.elnow,_sp.sampleStamp.temperature,\
			_sp.sampleStamp.freq0,_sp.sampleStamp.av,_sp.sampleStamp.avc,\
			_sp.sampleStamp.nfreq,_sp.sampleStamp.freqsep)
			_specs = ARIAPI.specs(_stamp,\
			_sp.spec,_sp.avspec,_sp.avspecc,_sp.specd)
			lastSpectrum[_sp.sampleStamp.name.upper()] = _specs
		return lastSpectrum
		
	def getLastSHSpectrum(self, current = None):
		lastSHSpectrum = {}
		_sp = self.obsMode.SHspectrum
		_stamp = ARIAPI.SHstamp(_sp.samplestamp.time,\
		_sp.samplestamp.seq,_sp.samplestamp.freqi,\
		_sp.samplestamp.freqf, _sp.samplestamp.channels,\
		_sp.samplestamp.chbw, self.obsMode.SpectralPower[0], self.obsMode.SpectralPower[1],\
		self.obsMode.Clientstatus['SRT1'].aznow, self.obsMode.Clientstatus['SRT1'].elnow,\
		self.obsMode.Clientstatus['SRT2'].aznow, self.obsMode.Clientstatus['SRT2'].elnow, \
		self.obsMode.Clientstatus['SRT1'].az, self.obsMode.Clientstatus['SRT1'].el)
		lastSHSpectrum['SH'] = ARIAPI.SHspectrum(_stamp, _sp.SHspec)
		return lastSHSpectrum
try:
	if len(sys.argv)<2:
		print "use SRTcontrolServer.py  -h 192.168.0.6 -p 10000"
		sys.exit()
	IP =  ' '.join(sys.argv[1:])
	IP = "default -h " + IP
except:
	print "use SRTcontrolServer.py default -h 192.168.0.6 -p 10000 or 10001"

status = 0
ic = None
#IP = 'default -h 192.168.0.6 -p 10015'
IP = 'default -h '+ IP

try:
	#ic = Ice.initialize(sys.argv)
	ic = Ice.initialize([''])
	#adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.6 -p 10000")
	adapter = ic.createObjectAdapterWithEndpoints("ARIAPI", IP)
	object = ARIAPII()
	adapter.add(object, ic.stringToIdentity("ARIAPI"))
	adapter.activate()
	print "ARI ICE API server up and running!"
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

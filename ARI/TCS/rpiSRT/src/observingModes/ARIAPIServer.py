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
			target = list(target)
		self.obsMode.obswArray(mode, target)
		msg = "Commanding array"
	
	def setRxArray(self, freq, RxMode, current = None):
		self.obsMode.radioSetup(freq, RxMode)
		msg = "Receiver and Target Set"
		print msg
		return msg
		
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
		self.obsMode.npointScanMap(self, points, delta, spec)
		msg = "Executing n-points Scan Map"
		print msg
		return msg
	
	def findRaDecSources(self, current = None):
		sources = sites.find_radec(True)
		return sources

	def findPlanets(self, current = None):
		sources = sites.find_planets(True)
		return sources

	def findStars(self, current = None):
		sources = sites.find_stars(True)
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
		self.states()
		msg = "Getting observing mode state"
		return msg

	def getArrayState(self, current = None):
		msg = "Getting array state"
		return msg


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

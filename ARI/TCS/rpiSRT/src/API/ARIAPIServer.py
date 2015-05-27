import sys, traceback, Ice
#sys.path.insert(0,'../clients/SRT_client/')

from time import sleep
import ARIAPI
import obsmodeV03_APItest as ARIobsMode
import threading
import os
import socket
import sites

class ARIAPII(ARIAPI.API):
	def __init__(self):
		self.ARI_nodes = {'SRT1':'localhost -p 10011',
			'SRT2':'localhost -p 10012',
			'SH':'localhost -p 10013',
			'ROACH':'localhost -p 10014'
			}
		self.antenna = ''
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars
		self.SRTsources = sites.SRTsources
		#print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		#print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		#print str(len(self.SRTsources))+ " observable SRT sources: " + str(self.SRTsources.keys())	
		self.initialized = False
		self.radio_config = False
		self.freq = 1420.4
		self.rec_mode = 1
		self.new_freq = 1420.4
		self.new_rec_mode = 1
		self.tracking = False
		self.OnSource = False
		self.Target = ""
        def sayHello(self, current=None):
                print ">>>>>>>>>>>>>>>>>>>>>>>.. say Hello"
		
	def setup(self, current = None):
		self.setIP(self.antennaIP)
		self.connect()
		self.SetSerialPort(self.serialport)
		print "sending antenna to Stow"
		self.Init(self.parameters)
		while(not self.initialized):
			sleep(1)
		return "Antenna initialized and in stow position"
	
	def trackSource(self, s, current = None):
		self.tracking(s)
		while(not self.OnSource):
			sleep(1)
		return "Tracking source"
	
	def stopTrack(self, current = None):
		self.Stop()
		return "Track Stopped"

	def testConn(self, s, current = None):
		print s
		return s


	def ChooseObservingMode(self, s1, s2, current = None):
		if (s1 == "SD"):
			if (s2 == "Double"):
				self.obsMode = ARIobsMode.SRTDoubleSingleDish()
				msg = "Double Single Dish Mode chosen"
			else:
				self.obsMode = aRIobsMode.SRTSingleDish(s2)
				msg = "Single Dish Mode chosen with " + s2
		elif (s1 == "ARI"):
			if (s2 == "SH"):
				self.obsMode = AIRobsMode.ARI_SignalHound()
				msg = "ARI Signal Hound Mode chosen"
			elif (s2 == "ROACH"):
				self.obsMode = AIRobsMode.ARI_ROACH()
				msg = "ARI ROACH Mode chosen"
		else:
			msg = "error in parameters"	
		print msg
		return msg
		
	def Connect(self, current = None):
		self.obsMode.createObsMode()
		msg = "Observing Mode Created"
		print msg
		return msg
	
	def Initialize(self, current = None):
		self.obsMode.setup()
		msg = "Telescope Initialized"
		print msg
		return msg
	
	def SetTarget(self, s1, s2, s3, current = None):
		self.obsMode.radioSetup(s2, s3)
		self.Target = s1
		msg = "Receiver and Target Set"
		print msg
		return msg
	
	def StartTracking(self, current = None):
		self.obsMode.trackSource(self.Target)
		msg = "Tracking Source"
		print msg
		return msg
	
	def StopTracking(self, current = None):
		self.obsMode.stopTrack()
		msg = "Track source stopped"
		print msg
		return msg
	
	def FindSources(self, current = None):
		sources = sites.find_SRTSources(sites.SRTSources_list, sites.site)
		return sources


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
#IP = 'default -h 192.168.3.100 -p 10015'
IP = 'default -h '+ IP
print IP

try:
	#ic = Ice.initialize(sys.argv)
	ic = Ice.initialize([''])
	#adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.6 -p 10000")
	adapter = ic.createObjectAdapterWithEndpoints("ARIAPI", IP)

    #hostname = "192.168.1.111"
    #endpoint = "tcp -h %s -p 10000:udp -h %s -p 10000:ws -h %s -p 10002" % (hostname, hostname, hostname)
	#adapter = ic.createObjectAdapterWithEndpoints("API", endpoint)
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

import sys, traceback, Ice
import time


sys.path.append('./IceClients/')
import SRTClient
import sites

class ObsBase():
	def __init__(self):
		self.ARI_nodes = {'SRT1':'localhost -p 10011',
			'SRT2':'localhost -p 10012',
			'SH':'localhost -p 10013',
			'ROACH':'localhost -p 10014'
			}
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars
		self.SRTsources = sites.SRTsources
		print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		print str(len(self.SRTsources))+ " observable SRT sources: " + str(self.SRTsources.keys())	

	def find_planets(self):
		self.planets = sites.find_planets(sites.planet_list, self.site)
		print str(len(self.planets))+ " observabable planets: " + str(self.planets)
		
	def find_stars(self):
		self.stars = sites.find_stars(sites.star_list, self.site)
		print str(len(self.stars)) + " observabable stars: " + str(self.stars)
		
	def find_SRTsources(self):
		#This method search for sources in RaDec originally defined in the SRT.cat file
		self.SRTsources = sites.find_SRTsources(sites.SRT_sources_list, self.site)
		print str(len(self.SRTsources)) + " observabable SRT sources: " + str(self.SRTsources)		

	def clean(self):
		try:
			self.srt1 = None
		except:
			pass
		try:
			self.srt2 = None
		except:
			pass
		try:
			self.SH = None
		except:
			pass
		try:
			self.ROACH = None
		except:
			pass

	def connect(self, IP):
		#client connection routine to server
		#global statusIC
		#global ic
		#global controller
		statusIC = 0
		try:
			# Reading configuration info
			#configPath = os.environ.get("SWROOT")
			#configPath = configPath + "/config/LCU-config"
			initData = Ice.InitializationData()
			initData.properties = Ice.createProperties()
			#initData.properties.load('IceConfig')
			ic = Ice.initialize(sys.argv, initData)
			# Create proxy
			#base = ic.stringToProxy("SRTController:default -h 192.168.0.6 -p 10000")
			IP_string = "SRTClient:default -h " + IP
			base = ic.stringToProxy(IP_string)
			self.controller = SRTClient.ClientPrx.checkedCast(base)
			self.controller.begin_message("connected to client", self.genericCB, self.failureCB);
			print "Connecting to SRTClient"
			#self.controller.begin_serverState(self.serverCB, self.failureCB);
			if not self.controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			self.statusIC = 1
			sys.exit(statusIC)
		return
		
	def failureCB(self, ex):
		#failure Callback
		print "Exception is: " + str(ex)
		return
		
	def genericCB(self, a):
		#generic callback
		print a
		return	

	def setupCB(self, a):
		#generic callback
		print a
		print "Setup finished"
		return	


class SRTSingleDish(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
			
	def setup(self, antenna):
		self.connect(self.ARI_nodes[antenna])
		statusIC = 0
		ic = None
		try:
			self.controller.begin_setup(self.setupCB, self.failureCB);
			print "initializing antenna"
		except:
			traceback.print_exc()
			self.statusIC = 1


	def trackSource(self, target):
		statusIC = 0
		ic = None
		try:
			self.controller.begin_tracking(target, self.trackCB, self.failureCB);
			print "moving antenna to target"
		except:
			traceback.print_exc()
			self.statusIC = 1		
	
	def trackCB(a):
		print a
		print "Antenna on source"
		
	
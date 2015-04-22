import sys, traceback, Ice
import time


sys.path.append('../IceClients/')
import SRTClient
import sites


antenna = ''
class ObsBase():
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
			self.ARI_controllers = None
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
			IP_string = "SRTClient:default -h " + IP
			base = ic.stringToProxy(IP_string)
			controller = "controller " + IP_string
			print "Connecting to SRTClient"
			#self.controller.begin_serverState(self.serverCB, self.failureCB);
			if not controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			self.statusIC = 1
			sys.exit(statusIC)
		return controller
		
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
		self.initialized = True
		return	

	def createObsMode(self):
		self.ARI_controllers = {}
		for node in self.nodes:
			print "Connecting to "+ node
			controller = self.connect(self.ARI_nodes[node])
			self.ARI_controllers[node] = controller
	
	def setup(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				print "initializing antenna " + node
				self.setupCB("Antenna initialized and in stow position")
		except:
			traceback.print_exc()
			self.statusIC = 1

	def trackSource(self, target):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:				
				print "moving antenna" + node + " to target"
				self.trackCB("Tracking source")
			self.tracking
		except:
			traceback.print_exc()
			self.statusIC = 1		
	
	def trackCB(self, a):
		print a
		print "Antenna on source"
		self.OnSource
		
	def stopTrack(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				print "Stopping Antenna " + node
				self.stopTrackCB("Track Stopped")
		except:
			traceback.print_exc()
			self.statusIC = 1		
	
	def stopTrackCB(self, a):
		print a
		print "Antenna Stopped"


class SRTSingleDish(ObsBase):
	def __init__(self, antenna):
		ObsBase.__init__(self)	
		self.nodes = [antenna]
				
	def radioSetup(self, freq, rec_mode):
		statusIC = 0
		ic = None
		try:
			self.new_freq = freq
			self.new_rec_mode = rec_mode
			print "setting receiver"
			self.rsetupCB("frequency and mode set")
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def set_freq(self, freq):
		self.radioSetup(freq, self.rec_mode)
		
	def set_mode(self, rec_mode):
		self.radioSetup(self.freq, rec_mode)
			
	def rsetupCB(self,a):
		#generic callback
		print a
		print "Setup finished"
		self.radio_config= True
		self.freq = self.new_freq
		self.rec_mode = self.new_rec_mode
		return	
		
	def status(self):
		statusList = [self.initialized, self.radio_config, self.freq, self.rec_mode, self.new_freq, self.new_rec_mode, self.tracking,self.OnSource]
		return statusList


class SRTDoubleSingleDish(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		self.nodes = ['SRT1', 'SRT2']
		
	def radioSetup(self, freq, rec_mode):
		statusIC = 0
		ic = None
		try:
			self.new_freq = freq
			self.new_rec_mode = rec_mode
			for node in self.nodes:
				print "setting receiver " + node
				self.rsetupCB("frequency and mode set")
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def set_freq(self, freq):
		self.radioSetup(freq, self.rec_mode)
		
	def set_mode(self, rec_mode):
		self.radioSetup(self.freq, rec_mode)
			
	def rsetupCB(self,a):
		#generic callback
		print a
		print "Setup finished"
		self.radio_config= True
		self.freq = self.new_freq
		self.rec_mode = self.new_rec_mode
		return	

		
	def status(self):
		statusList = [self.initialized, self.radio_config, self.freq, self.rec_mode, self.new_freq, self.new_rec_mode, self.tracking,self.OnSource]
		return statusList	

	
class ARI_SignalHound(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		self.nodes =['SRT1', 'SRT2', 'SH']
	
class ARI_ROACH(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		self.nodes =['SRT1', 'SRT2', 'ROACH']



	
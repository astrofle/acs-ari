import sys, traceback, Ice
import time
import SRTClient
import sites

class ARI_obsmodes():
	def __init__(self):
		self.ARI_nodes = {'SRT1':'localhost -p 10010',
			'SRT2':'localhost -p 10011',
			'SH':'localhost -p 10012',
			'ROACH':'localhost -p 10013'
			}
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars
		print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())

	def find_planets(self):
		self.planets = sites.find_planets(sites.planet_list, self.site)
		print str(len(self.planets))+ " observabable planets: " + str(self.planets)
		
	def find_stars(self):
		self.stars = sites.find_stars(sites.star_list, self.site)
		print str(len(self.stars)) + " observabable stars: " + str(self.stars)

	def SRTAntennas(self):
		self.srt1 = SRT() # control for a single antenna
		self.srt1.setIP(self.ARI_nodes['SRT1'])
		self.srt1.connect()
		time.sleep(2)
		self.srt2 = SRT()
		self.srt2.setIP(self.ARI_nodes['SRT2'])
		self.srt2.connect()
		time.sleep(2)
		
	def SingleDishSRT(self, SRT_antenna, source):
		print "This is the Single Dish SRT Observing mode"
		self.srt1 =  self.connect(self.ARI_nodes[SRT_antenna])
		statusIC = 0
		ic = None
		try:
			self.srt1.begin_setup(self.genericCB, self.failureCB);
			print "initializing antenna"
		except:
			traceback.print_exc()
			self.statusIC = 1		
		try:
			self.srt1.begin_tracking(self.genericCB, self.failureCB)
			print "Going to source", source
		except:
			traceback.print_exc()
			self.statusIC = 1

		
	def DoubleSingleDishSRT(self):
		print "This is the Double Single Dish SRT Observing mode"
		self.SRTAntennas()
					
	def ARI_SH(self):
		print "This is the ARI - Signal Hound Observing mode"
		self.SRTAntennas()
		self.sh = SH() # control for signal hound
		self.sh.setIP(self.ARI_nodes['SH'])
		self.sh.connect()
		self.sh.Message('hola')
		time.sleep(2)

	def ARI_ROACH(self):
		print "This is the ARI - ROACH Observing mode"
		self.SRTAntennas()
		roach = ROACH() # control for signal hound
		roach.connect()
		roach.Message('hola')
	
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
			initData.properties.load('IceConfig')
			ic = Ice.initialize(sys.argv, initData)
			# Create proxy
			#base = ic.stringToProxy("SRTController:default -h 192.168.0.6 -p 10000")
			IP_string = "SRTClient:default -h " + IP
			base = ic.stringToProxy(IP_string)
			controller = SRTClient.ClientPrx.checkedCast(base)
			controller.begin_message("connected to client", self.genericCB, self.failureCB);
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



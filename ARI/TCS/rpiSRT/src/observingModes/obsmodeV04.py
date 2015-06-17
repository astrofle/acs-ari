import sys, traceback, Ice
import time


sys.path.append('../IceClients/')
import SRTClient
import sites

import SHControl
import threading

antenna = ''
class ObsBase():
	def __init__(self):
		self.ARI_nodes = {
		'SRT1':"SRTClient:default -h localhost -p 10011",
		'SRT2':"SRTClient:default -h localhost -p 10012",
		'SH':"SHController:default -h localhost -p 10013",
		'ROACH':"SRTClient:default -h localhost -p 10014"
		}
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
		self.tracking = False
		self.OnSource = False
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
		self.Clientstatus ={}
		self.getClStatus = True
		####
		
		
	def find_planets(self, disp):
		self.planets = sites.find_planets(sites.planet_list, self.site, disp)
		print str(len(self.planets))+ " observabable planets: " + str(self.planets)
		
	def find_stars(self, disp):
		self.stars = sites.find_stars(sites.star_list, self.site, disp)
		print str(len(self.stars)) + " observabable stars: " + str(self.stars)
	
	def find_radec(self, disp):
		self.radecSources = sites.find_SRTsources(sites.SRTsources, sites.site, disp)
		print str(len(self.radecSources)) + " observabable stars: " + str(self.radecSources)

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
			#base = ic.stringToProxy("SRTController:default -h 192.168.0.6 -p 10000")
			IP_string = IP
			#IP_string = "SRTClient:default -h " + IP
			base = ic.stringToProxy(IP_string)
			if IP_string.startswith('SRT'):
				controller = SRTClient.ClientPrx.checkedCast(base)
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Connecting to SRT Client"
			if IP_string.startswith('SH'):
				controller = SHControl.SignalHoundPrx.checkedCast(base)
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Connecting to Signal hound Client"
			controller.begin_message("connected to client", self.genericCB, self.failureCB);

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
	
	def createObsMode(self):
		self.ARI_controllers = {}
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" creating "+ self.observingMode
		for node in self.nodes:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Connecting to "+ node
			controller = self.connect(self.ARI_nodes[node])
			self.ARI_controllers[node] = controller
			if node.startswith('SRT'):
			#Set SRT receiver switch mode
				self.ARI_controllers[node].begin_setRxMode(self.mode, self.modeCB, self.failureCB);
			ClientStatus_Thread = threading.Thread(target = self.getClientStatusThread, name='Clientstatus')
			ClientStatus_Thread.start()
			print "starting status thread"

	def modeCB(self, a):
		print a
		antenna = a.split(' ')[2].upper()
		mode = a.split(' ')[-1]
		self.RxSwmode[antenna] = mode

	def SwRxMode(self, node, mode):
		self.ARI_controllers[node].begin_setRxMode(mode, self.modeCB, self.failureCB);

	def setup(self):
		statusIC = 0
		ic = None
		if self.setupInProgress:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " setup process in progress, wait"
			return
		else:
			self.setupInProgress = True
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_setup(self.setupCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" initializing antenna " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def setupCB(self, a):
		#generic callback
		print a
		antenna = a.split(' ')[2].upper()
		self.initialized[antenna] = True
		self.atStow[antenna] = True
		initnodes = 0
		for node in self.nodes:
		    if (self.initialized[node]):
		        initnodes += 1

		if initnodes == len(self.nodes):
			self.setupInProgress = False
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Initialization complete"
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " Initialization in progress"
		return

	def Stow(self):
		statusIC = 0
		ic = None
		if self.stowInProgress:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " Stow in progress, wait"
			return
		else:
			self.stowInProgress = True
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_SRTStow(self.stowCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Stowing Antenna: " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
    
	def stowCB(self, a):
		print a
		antenna = a.split(' ')[2].upper()
		self.atStow[antenna] = True
		stownodes = 0
		for node in self.nodes:
		    if (self.atStow[node]):
		        stownodes += 1
		if stownodes == len(self.nodes):
			self.stowInProgress = False
		return
		
	def getClientStatusThread(self):
		while(self.getClStatus):
			self.getClientStatus()
			time.sleep(2)
	
	def getClientStatus(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_SRTstate(self.getClientStatusCB, self.failureCB);
					#print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Getting status: " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def getClientStatusCB(self, a):
		node = a.name.upper()
		self.Clientstatus[node] = a
#####Antenna Operation##################################################
	def obswSRT(self, mode, target):
		statusIC = 0
		ic = None
		self.onSource = False
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_obsSRT(mode, str(target), self.trackCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" moving antenna" + node + " to target"
			self.tracking
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	
	def trackCB(self, a):
		print a
		name = a.split()
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Antenna on source"
		if self.observingMode == 'SRT-SD':
			self.OnSource = True
		elif self.observingMode == 'SRT-DSD':
			if name == 'srt1':
				self.OnSrc[0] = 1
			elif name == 'srt2':
				self.OnSrc[1] = 1
		if sum(self.OnSrc) == 2:
			self.OnSrc =[0,0]
			self.OnSource = True
		#call by getSpectrum

	
	def stopSRT(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_StopObs(self.stopTrackCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Stopping Antenna " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def stopTrackCB(self, a):
		print a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Antenna Stopped"
##################################################

	def shutdown(self):
		#status thread
		self.getClStatus = False
	
	
class SRTSingleDish(ObsBase):
	def __init__(self, antenna):
		ObsBase.__init__(self)
		self.nodes = [antenna]
		self.observingMode = 'SRT-SD'
		self.mode = 'SD'
		
	def radioSetup(self, freq, rec_mode):
		statusIC = 0
		ic = None
		try:
			self.new_freq = freq
			self.new_rec_mode = str(rec_mode)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + str(self.nodes)+" "+ "setting receiver"
			self.ARI_controllers[self.nodes[0]].begin_setFreq(self.new_freq, self.new_rec_mode, self.rsetupCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def set_freq(self, freq):
		self.radioSetup(freq, self.rec_mode)
		
	def set_mode(self, rec_mode):
		self.radioSetup(self.freq, str(rec_mode))
			
	def rsetupCB(self,a):
		#generic callback
		print a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ str(self.nodes)+ "Setup finished"
		self.radio_config= True
		self.freq = self.new_freq
		self.rec_mode = self.new_rec_mode
		self.RxSetup[self.nodes[0]] = [self.freq, self.rec_mode]
		return
		
	def status(self):
		statusList = [self.initialized, self.radio_config, self.freq, self.rec_mode, self.new_freq, self.new_rec_mode, self.tracking,self.OnSource]
		return statusList

	def states(self):
		print "observing mode:"+ str(self.observingMode)
		print "nodes:"+ str(self.nodes)
		print "Ari_controllers:"+ str(self.ARI_controllers)
		#serverstate??
		print "setup in progress:"+ str(self.setupInProgress)
		print "initialized:"+ str(self.initialized)
		print "atStow:"+ str(self.atStow)
		print "stow in progress:"+ str(self.stowInProgress)
		print "mode:"+ str(self.mode)
		print "Rx Switch mode:"+ str(self.RxSwmode)
		print "SRT Rx setup:" + str(self.RxSetup)
		print "get Client status:"+ str(self.getClStatus)



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

	def connect(self, IP, node):
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
			self.ics[node] = ic
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
		
	def disconnect(self):
		#disconnection routine
		for node in self.nodes:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +node+" Disconnecting.."
			if self.ics[node]:
				try:
					self.ics[node].destroy()
				except:
					traceback.print_exc()
					self.statusIC = 1
					sys.exit(status)
		return
	
	def ClientShutdown(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_ClientShutdown(self.genericCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
					" initializing antenna " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
	
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
			controller = self.connect(self.ARI_nodes[node], node)
			self.ARI_controllers[node] = controller
			if node.startswith('SRT'):
			#Set SRT receiver switch mode
				self.ARI_controllers[node].begin_setRxMode(self.mode, self.modeCB, self.failureCB);
		
		ClientStatus_Thread = threading.Thread(target = self.getClientStatusThread, name='Clientstatus')
		ClientStatus_Thread.start()
		print "starting status thread"
		time.sleep(1)
		for node in self.nodes:
			if (self.Clientstatus[node].SRTinitialized == 'True'):
				print node + " is initialized - setup not needed - see self.Clientstatus for node status"
			else:
				print node + " requires initialization - do self.setup() "

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
					self.ArrayOnTarget[node] = False
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
		#if ((float(self.Clientstatus[node].az) - float(self.Clientstatus[node].aznow)) >= 3.5):
		#	self.ArrayOnTarget[node] = False
#####Antenna Operation##################################################
	def obswArray(self, mode, target):
		statusIC = 0
		ic = None
		if self.ArrayMovingToTarget:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Array is moving, wait or command Stop before"
			return
		else:
			self.ArrayStopCmd = False
			self.ArrayMovingToTarget = True
		try:
			
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ArrayOnTarget[node] = False
					self.ARI_controllers[node].begin_obsSRT(mode, str(target), self.trackCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" moving antenna" + node + " to target"
			OnTrg_Thread = threading.Thread(target = self.onTarget_Thread, name='onTarget')
			OnTrg_Thread.start()
			print "starting onTarget thread"
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	
	def trackCB(self, a):
		print a
		
	def onTarget_Thread(self):
		while(self.ArrayMovingToTarget):
			onTargetnodes = 0
			time.sleep(2)
			for node in self.nodes:
				self.ArrayOnTarget[node] = self.Clientstatus[node].SRTonTarget
				if (self.ArrayOnTarget[node] == 'True'):
					onTargetnodes += 1
				if ((node == 'SH') or (node == 'ROACH')):
					onTargetnodes += 1
				if onTargetnodes == len(self.nodes):
					self.ArrayMovingToTarget = False
			time.sleep(1)
		if self.ArrayStopCmd:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Array command to stop"
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Array on Target"
	
	def stopArray(self):
	#Stop array to track a target - mandatory for pointing the array to a different target
		statusIC = 0
		ic = None
		try:
			self.ArrayStopCmd = True
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
		self.ArrayMovingToTarget = False
		
	def stopGoingtoTarget(self):
	#Stops array to a target - use it only for this purpose - StopArray is still needed after this.
	#Does not work for stopping stow
		statusIC = 0
		ic = None
		try:
			self.ArrayStopCmd = True
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_SRTStopGoingToTarget(self.stopTrackCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Stopping Antenna " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def StopTargetCB(self,a):
		print a
		
	def SetOffsetPointing(self, azoff, eloff):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				self.offsets = [azoff, eloff]
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"setting pointing offset"
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_offsetPointing(azoff, eloff, self.offsetCB, self.failureCB);
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def offsetCB(self,a):
		print a
		
	def npointScanMap(self, points, delta, spec):
		statusIC = 0
		ic = None
		if self.scanMapInProgress:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " Scan map is in progress, wait"
			return
		else:
			self.scanMapInProgress = True
		try:
			for node in self.nodes:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"setting pointing offset"
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_NpointScan(points, delta, spec, self.nscanCB, self.failureCB);
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def nscanCB(self,a):
		print  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + "scan completed"
		self.scanMapInProgress = False
		self.map = a
		
		

######################### Receiver spectrum
	def getSpectrum(self):
		while(self.readSpectrum):
			statusIC = 0
			ic = None
			try:
				for node in self.nodes:
					self.NewSpectrum[node] = False
					self.waitSpectrum = True
					if node.startswith('SRT'):
						self.ARI_controllers[node].begin_getSpectrum(self.spectrumCB, self.failureCB);
						print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ node + " Getting spectrum"
				while(self.waitSpectrum):
					time.sleep(1)
			except:
				traceback.print_exc()
				self.statusIC = 1
		
	def spectrumCB(self, sp):
		self.spec = sp
		#self.spectrum[sp.sampleStamp.name] = self.spec
		name = sp.sampleStamp.name.upper()  
		tim = sp.sampleStamp.timdate
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+name + " Spectrum Obtained"
		print name+" "+tim
		self.spectrum[name] = self.spec
		self.NewSpectrum[name] = True
		spNodes = 0
		for node in self.nodes:
			if self.NewSpectrum[node]:
				spNodes += 1
		if (spNodes == len(self.nodes)):
			self.waitSpectrum = False
		return
		
	def enableSpectrum(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				self.readSpectrum = True
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ node + " starting spectrum reading"
				self.ARI_controllers[node].begin_startSpectrum(self.stopspCB, self.failureCB)
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+node+" starting spectrum reading thread"
			getSpec_thread = threading.Thread(target = self.getSpectrum, name = 'getSpecLoop')
			getSpec_thread.start()
		except:
			traceback.print_exc()
			self.statusIC = 1

	def stopspCB(self, a):
		print a
		return

	def disableSpectrum(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				print time.strftime('%Y-%m# -%d %H:%M:%S', time.localtime())+" stopping spectrum reading"
				self.ARI_controllers[node].begin_stopSpectrum(self.stopspCB, self.failureCB)
				self.readSpectrum = False
				self.waitSpectrum = False
		except:
			traceback.print_exc()
			self.statusIC = 1



##################################################

	def shutdown(self):
		#status thread
		self.getClStatus = False
		#OnTarget Thread
		self.ArrayMovingToTarget = False
		#spectrum Thread
		self.readSpectrum = False
		self.waitSpectrum = False
		#disconnect
		self.disconnect()
	
	def ClientThreads(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].ClientThreads();
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Client threads"
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def states(self):
		print "observing mode:"+ str(self.observingMode)
		print "nodes:"+ str(self.nodes)
		print "ARI_controllers:"+ str(self.ARI_controllers)
		print "setup in progress:"+ str(self.setupInProgress)
		print "initialized:"+ str(self.initialized)
		print "atStow:"+ str(self.atStow)
		print "stow in progress:"+ str(self.stowInProgress)
		print "mode:"+ str(self.mode)
		print "Rx Switch mode:"+ str(self.RxSwmode)
		print "SRT Rx setup:" + str(self.RxSetup)
		print "Array frequency:" + str(self.new_freq)
		print "Array Rx Mode:" + str(self.new_rec_mode)
		print "get Client status:"+ str(self.getClStatus)
		print "Array moving to target:"+ str(self.ArrayMovingToTarget)
		print "Array on Target:"+ str(self.ArrayOnTarget)
		print "Array Stop Command:"+ str(self.ArrayStopCmd)
		print "Array offsets:" + str(self.offsets)
		print "Scan map in progress: "+ str(self.scanMapInProgress)
		print "Read spectrum: " + str(self.readSpectrum)
		print "new spectrum to read: " + str(self.NewSpectrum)
		print "Waiting spectrum: " + str(self.waitSpectrum)

	
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
		
class SRTDoubleSingleDish(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		self.nodes = ['SRT1', 'SRT2']
		self.observingMode = 'SRT-DSD'
		self.mode = 'SD'
	
	def radioSetup(self, freq, rec_mode):
		statusIC = 0
		ic = None
		try:
			self.new_freq = freq
			self.new_rec_mode = str(rec_mode)
			for node in self.nodes:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " "+node+" "+"setting receiver "
				self.ARI_controllers[node].begin_setFreq(self.new_freq, self.new_rec_mode, self.rsetupCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def set_freq(self, freq):
		self.radioSetup(freq, self.rec_mode)
		
	def set_mode(self, rec_mode):
		self.radioSetup(self.freq, rec_mode)
			
	def rsetupCB(self,a):
		#generic callback
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " "+a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " Radio Setup finished"
		self.radio_config= True
		self.freq = self.new_freq
		self.rec_mode = self.new_rec_mode
		return




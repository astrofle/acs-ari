import sys, traceback, Ice
import time


sys.path.append('../IceClients/')
import SRTClient
import ARIAPI
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
		'SRT2':False,
		'SH' : False
		}
		self.ArrayMovingToTarget = False
		self.ArrayStopCmd = False
		self.Clientstatus ={}
		self.getClStatus = True
		self.offsets = [0,0]
		self.map = {}
		self.ArrayscanMapInProgress = False
		self.scanMapInProgress = {
		'SRT1':False,
		'SRT2':False
		}
		self.SMCheckTh_initialized = False
		self.readSpectrum
		self.radecSources =[]
		self.ARI_controllers = {}
		self.ARI_controllersTXT = {}
		####
		self.SpectralPower = []
		####
		# Callback functions - dictionaries
		self.SwModeCB = {
		'SRT1': self.SwModeSRT1CB,
		'SRT2': self.SwModeSRT2CB
		}
		self.SetupNodesCB = {
		'SRT1': self.setupSRT1CB,
		'SRT2': self.setupSRT2CB,
		}
		
		self.StowNodeCB = {
		'SRT1': self.stowSRT1CB,
		'SRT2': self.stowSRT2CB
		}
		
		self.getNodeClientStatusCB = {
		'SRT1': self.getClientStatusSRT1,
		'SRT2': self.getClientStatusSRT2,
		'SH': self.getClientStatusSH
		}
		
		self.nodeStopTrackCB = {
		'SRT1': self.stopTrackSRT1CB,
		'SRT2': self.stopTrackSRT2CB
		}
		
		self.stopFlag = {
		'SRT1': False,
		'SRT2': False
		}
		
		self.nodeNScanCB = {
		'SRT1': self.nScanSRT1CB,
		'SRT2': self.nScanSRT2CB
		}
		
		self.getNodeSpectrumCB = {
		'SRT1': self.getSpectrumSRT1CB,
		'SRT2': self.getSpectrumSRT2CB
		}
		
		self.calcons = {
		'SRT1': 1.0,
		'SRT2': 1.0
		}
		
		self.calibrated = {
		'SRT1': False,
		'SRT2': False
		}
		
		self.calibrationCB = {
		'SRT1': self.calibSRT1CB,
		'SRT2': self.calibSRT2CB
		}
		
		self.CalibrationInProgress = False
		
	def find_planets(self, disp):
		self.planets = sites.find_planets(sites.planet_list, self.site, disp)
		print str(len(self.planets))+ " observabable planets: " + str(self.planets)
		
	def find_stars(self, disp):
		self.stars = sites.find_stars(sites.star_list, self.site, disp)
		print str(len(self.stars)) + " observabable stars: " + str(self.stars)
	
	def find_radec(self, disp):
		self.radecSources = sites.find_SRTsources(sites.SRTsources, sites.site, disp)
		if disp:
			print str(len(self.radecSources)) + " observabable stars: " +\
			str(self.radecSources)
		return

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
					self.ARI_controllers[node].\
					begin_ClientShutdown(self.genericCB, self.failureCB);
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
		self.ARI_controllersTXT = {}
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
		" creating "+ self.observingMode
		for node in self.nodes:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
			" Connecting to "+ node
			controller = self.connect(self.ARI_nodes[node], node)
			self.ARI_controllers[node] = controller
			self.ARI_controllersTXT[node] = str(controller)
			if node.startswith('SRT'):
			#Set SRT receiver switch mode
				self.ARI_controllers[node].\
				begin_setRxMode(self.mode, self.SwModeCB[node], self.failureCB)
		
		ClientStatus_Thread = threading.Thread(target = \
		self.getClientStatusThread, name='Clientstatus')
		ClientStatus_Thread.start()
		print "starting status thread"
		time.sleep(1)
		for node in self.nodes:
			if node.startswith('SRT'):
				if (self.Clientstatus[node].initialized):
					print node + " is initialized - setup not needed - \
					see self.Clientstatus for node status"
				else:
					print node + " requires initialization - do self.setup() "
			if node == 'SH':
				if (self.Clientstatus[node].initialized):
					print node + " is initialized -- setup not needed - \
					see self.Clientstatus for node status"
				else:
					print node + " requires initialization - do self.setup() "
	
	def SwModeSRT1CB(self, a):
		print a
		antenna = a.split(' ')[2].upper()
		mode = a.split(' ')[-1]
		self.RxSwmode[antenna] = mode
		
	def SwModeSRT2CB(self, a):
		print a
		antenna = a.split(' ')[2].upper()
		mode = a.split(' ')[-1]
		self.RxSwmode[antenna] = mode
	
	def SwRxMode(self, node, mode):
		self.ARI_controllers[node].begin_setRxMode(mode, self.SwModeCB[node], self.failureCB);

	def setup(self):
		statusIC = 0
		ic = None
		if self.setupInProgress:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ \
			" setup process in progress, wait"
			return
		else:
			self.setupInProgress = True
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_setup(self.SetupNodesCB[node], self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ \
					" initializing antenna " + node
				elif (node == 'SH'):
					self.initHound()
					while(not self.SH_initialized):
						time.sleep(0.5)
		except:
			traceback.print_exc()
			self.statusIC = 1
			
		
	def setupSRT1CB(self, a):
		#generic callback
		print a
		antenna = a.split(' ')[2].upper()
		self.initialized[antenna] = True
		self.atStow[antenna] = True
		self.checkInit()
		return
	
	def setupSRT2CB(self, a):
		#generic callback
		print a
		antenna = a.split(' ')[2].upper()
		self.initialized[antenna] = True
		self.atStow[antenna] = True
		self.checkInit()
		return
	
	def checkInit(self):
		initnodes = 0
		for node in self.nodes:
		    if (self.initialized[node]):
		        initnodes += 1
		if initnodes == len(self.nodes):
			self.setupInProgress = False
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Initialization complete"
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " Initialization in progress"
		
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
					self.ARI_controllers[node].begin_SRTStow(self.StowNodeCB[node], self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Stowing Antenna: " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def stowSRT1CB(self, a):
		print a
		antenna = a.split(' ')[2].upper()
		self.atStow[antenna] = True
		self.checkStow()
		return
		
	def stowSRT2CB(self, a):
		print a
		antenna = a.split(' ')[2].upper()
		self.atStow[antenna] = True
		self.checkStow()
		return
	
	def checkStow(self):
		stownodes = 0
		for node in self.nodes:
			if node.startswith('SRT'):
			    if (self.atStow[node]):
			        stownodes += 1
			else:
				stownodes += 1
		if stownodes == len(self.nodes):
			self.stowInProgress = False
			print "Array at stow"
		return
		
	def SRTCalibration(self, method):
		statusIC = 0
		ic = None
		if self.CalibrationInProgress:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " Calibration in progress, wait"
			return
		else:
			self.CalibrationInProgress = True
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.calibrated[node] = False
					self.ARI_controllers[node].begin_SRTCalibration(method, self.calibrationCB[node], self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Calibrating Antenna: " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	def calibSRT1CB(self, calcons):
		print calcons
		self.calcons['SRT1'] = calcons
		self.calibrated['SRT1'] = True
		self.checkCalibration()
		return
		
	def calibSRT2CB(self, calcons):
		print calcons
		self.calcons['SRT2'] = calcons
		self.calibrated['SRT2'] = True
		self.checkCalibration()
		return
	
	def checkCalibration(self):
		calnodes = 0
		for node in self.nodes:
			if node.startswith('SRT'):
			    if (self.calibrated[node]):
			        calnodes += 1
			else:
				calnodes += 1
		if calnodes == len(self.nodes):
			self.CalibrationInProgress = False
			print "Array Calibrated (SRT receivers)"
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
					self.ARI_controllers[node].begin_SRTstate(self.getNodeClientStatusCB[node], self.failureCB);
					#print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Getting status: " + node
				if node == 'SH':
					self.ARI_controllers['SH'].begin_SHStatus(self.getNodeClientStatusCB[node], self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def getClientStatusSRT1(self, a):
		node = a.name.upper()
		self.Clientstatus[node] = a
		
	def getClientStatusSRT2(self, a):
		node = a.name.upper()
		self.Clientstatus[node] = a
		
	def getClientStatusSH(self, a):
		node = a.name.upper()
		self.Clientstatus[node] = a
		
#####Antenna Operation##################################################
	def obswArray(self, mode, target):
		statusIC = 0
		ic = None
		if self.ArrayMovingToTarget:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
			" Array is moving, wait or command Stop before"
			return
		else:
			self.ArrayStopCmd = False
			self.ArrayMovingToTarget = True
		try:
			
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ArrayOnTarget[node] = False
					self.ARI_controllers[node].begin_obsSRT(mode, str(target)\
					, self.trackCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" moving\
					antenna" + node + " to target"
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
				if node.startswith('SRT'):
					self.ArrayOnTarget[node] = self.Clientstatus[node].SRTonTarget
					if (self.ArrayOnTarget[node]):
						onTargetnodes += 1
				if ((node == 'SH') or (node == 'ROACH')):
					onTargetnodes += 1
				if onTargetnodes == len(self.nodes):
					self.ArrayMovingToTarget = False
			time.sleep(1)
		if self.ArrayStopCmd:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
			" Array command to stop"
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
			" Array on Target"
	
	def stopArray(self):
	#Stop array to track a target - mandatory for pointing the array to a different target
		statusIC = 0
		ic = None
		try:
			self.ArrayStopCmd = True
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_StopObs(self.nodeStopTrackCB[node],\
					self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
					" Stopping Antenna " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
	
		
	def stopTrackSRT1CB(self, a):
		print a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
		" Antenna Stopped"
		self.stopFlag['SRT1'] = True
		self.checkStop()

		
	def stopTrackSRT2CB(self, a):
		print a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
		" Antenna Stopped"
		self.stopFlag['SRT2'] = True
		self.checkStop()
	
	def checkStop(self):
		stopNodes = 0
		for node in self.nodes:
			if node.startswith('SRT'):
				if self.stopFlag[node]:
					stopNodes += 1
			else:
				stopNodes += 1
		if (stopNodes == len(self.nodes)):
			self.ArrayMovingToTarget = False
			print "Array stopped"
			self.stopFlag['SRT1']= False
			self.stopFlag['SRT2']= False
	
	def stopGoingtoTarget(self):
	#Stops array to a target - use it only for this purpose - StopArray is still needed after this.
	#Does not work for stopping stow
		statusIC = 0
		ic = None
		try:
			self.ArrayStopCmd = True
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_SRTStopGoingToTarget\
					(self.nodeStopTrackCB[node], self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
					" Stopping Antenna " + node
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
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
				"setting pointing offset"
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
		if self.ArrayscanMapInProgress:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
			" Scan map is in progress, wait"
			return
		else:
			self.ArrayscanMapInProgress = True
		try:
			for node in self.nodes:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
				"setting pointing offset"
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_NpointScan(points, delta, spec, self.nodeNScanCB[node], self.failureCB);
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	
	def nScanSRT1CB(self, a):
		print  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + "scan started"
		self.scanMapInProgress['SRT1'] = True
		self.map['SRT1'] = a
		self.checkMap()

	def nScanSRT2CB(self, a):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + "scan started"
		self.scanMapInProgress['SRT2'] = True
		self.map['SRT2'] = a
		time.sleep(1)
		self.checkMap()
	
	def checkMap(self):
		if not self.SMCheckTh_initialized:
			CMThread = threading.Thread(target = self.checkMap_thread, name = 'scanMapCheck')
			CMThread.start()
			self.SMCheckTh_initialized =  True
		
	def checkMap_thread(self):
		while(self.ArrayscanMapInProgress):
			sm = 0
			for node in self.nodes:
				if node.startswith('SRT'):
					self.scanMapInProgress[node] = self.ARI_controllers[node].NpointScanInProgress()
				if not self.scanMapInProgress[node]:
					sm +=1
				if node == 'SH':
					sm +=1
			if sm == len(self.nodes):
				print "Scan map finished"
				for node in self.nodes:
					if node.startswith('SRT'):
						self.map[node] = self.ARI_controllers[node].getNpointScanMap()
				self.ArrayscanMapInProgress = False
			time.sleep(5)

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
						self.ARI_controllers[node].begin_getSpectrum\
						(self.getNodeSpectrumCB[node], self.failureCB);
						print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
						" "+ node + " Getting spectrum"
				while(self.waitSpectrum):
					time.sleep(1)
			except:
				traceback.print_exc()
				self.statusIC = 1
	
	def getSpectrumSRT1CB(self, sp):
		self.spec = sp
		#self.spectrum[sp.sampleStamp.name] = self.spec
		name = sp.sampleStamp.name.upper()  
		tim = sp.sampleStamp.timdate
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+name + " Spectrum Obtained"
		print name+" "+tim
		self.spectrum[name] = self.spec
		self.NewSpectrum[name] = True
		self.checkSpectrum()
		return
		
	def getSpectrumSRT2CB(self, sp):
		self.spec = sp
		#self.spectrum[sp.sampleStamp.name] = self.spec
		name = sp.sampleStamp.name.upper()  
		tim = sp.sampleStamp.timdate
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+name + " Spectrum Obtained"
		print name+" "+tim
		self.spectrum[name] = self.spec
		self.NewSpectrum[name] = True
		self.checkSpectrum()
		return
	
	def checkSpectrum(self):
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
		if self.observingMode == 'ARI-SH':
			self.enableSHspectrum()
			self.ARI_SHSpectrum()
		else:
			try:
				for node in self.nodes:
					self.readSpectrum = True
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ node +\
					" starting spectrum reading"
					self.ARI_controllers[node].begin_startSpectrum(self.stopspCB,\
					self.failureCB)
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+node+\
					" starting spectrum reading thread"
				getSpec_thread = threading.Thread(target = self.getSpectrum, \
				name = 'getSpecLoop')
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
		if self.observingMode == 'ARI-SH':
			self.disableSHspectrum()
		else:
			try:
				for node in self.nodes:
					print time.strftime('%Y-%m# -%d %H:%M:%S', time.localtime())+\
					" stopping spectrum reading"
					self.ARI_controllers[node].begin_stopSpectrum(self.stopspCB, \
					self.failureCB)
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
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
					" Client threads"
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def states(self):
		print "observing mode:"+ str(self.observingMode)
		print "nodes:"+ str(self.nodes)
		print "ARI_controllers:"+ str(self.ARI_controllersTXT)
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
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
			" " + str(self.nodes)+" "+ "setting receiver"
			self.ARI_controllers[self.nodes[0]].begin_setFreq\
			(self.new_freq, self.new_rec_mode, self.rsetupCB, self.failureCB)
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
		name = a.split(' ')[2].upper()
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ \
		str(self.nodes)+ "Setup finished"
		self.radio_config= True
		self.freq = self.new_freq
		self.rec_mode = self.new_rec_mode
		self.RxSetup[name] = [ARIAPI.RxSet(self.freq, self.rec_mode)]
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
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+\
				" "+node+" "+"setting receiver "
				self.ARI_controllers[node].begin_setFreq\
				(self.new_freq, self.new_rec_mode, self.rsetupCB, self.failureCB)
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
		name = a.split(' ')[2].upper()
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+\
		str(self.nodes)+ "Setup finished"
		self.radio_config= True
		self.freq = self.new_freq
		self.rec_mode = self.new_rec_mode
		self.RxSetup[name] = [ARIAPI.RxSet(self.freq, self.rec_mode)]
		return

class ARI_SignalHound(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		#self.nodes =['SH']
		self.mode = 'ARI'
		self.nodes =['SRT1', 'SRT2', 'SH']
		self.observingMode = 'ARI-SH'
		self.SH_initialized = False
		self.bw = 40e6
		self.SH_bwSetup = False
		self.fc = 1421.0e6
		self.SH_fcSetup = False
		self.filename = "script_mode.txt"
		self.SH_filenameSetup = False
		self.SH_readSpectrum = False
		self.SH_headmade = False
		self.SH_spWritten = False
		self.SH_powerRead = False
		
	def initHound(self):
		statusIC = 0
		ic = None
		self.SH_initialized = False
		try:
			print "Initializing SignalHound"
			self.ARI_controllers['SH'].begin_SHinitHound(self.SHinitCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHinitCB(self, a):
		print a
		self.SH_initialized = True
		self.initialized['SH'] = True
		self.checkInit()

	def SH_setBW(self, bw):
		self.bw = bw
		statusIC = 0
		ic = None
		self.SH_bwSetup = False
		try:
			print "Set SignalHound BW"
			self.ARI_controllers['SH'].begin_SHsetBW(self.bw, self.SHBWCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHBWCB(self, a):
		print a
		self.SH_bwSetup = True
		
	def SH_setfc(self, fc):
		self.fc = fc
		statusIC = 0
		ic = None
		self.SH_fcSetup = False
		try:
			print "Set SignalHound central frequency"
			self.ARI_controllers['SH'].begin_SHsetFc(self.fc, self.SHfcCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHfcCB(self, a):
		print a
		self.SH_fcSetup = True

	def SH_setFileName(self, filename):
		self.filename = filename
		statusIC = 0
		ic = None
		self.SH_filenameSetup = False
		try:
			print "Set SignalHound spectrum filename"
			self.ARI_controllers['SH'].begin_SHsetFileName(self.filename,\
			self.SHfilenameCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHfilenameCB(self, a):
		print a
		self.SH_filenameSetup = True
		
	def SH_getSpectrum(self):
		statusIC = 0
		ic = None
		self.SH_readSpectrum = False
		try:
			print "Getting Signal hound spectrum"
			self.ARI_controllers['SH'].begin_SHgetSpectrum(self.SHspCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHspCB(self, a):
		self.SHspectrum = a
		self.SH_readSpectrum = True

	def SH_makeHead(self):
		statusIC = 0
		ic = None
		self.SH_headmade = False
		try:
			print "Creating header for spectrum file"
			self.ARI_controllers['SH'].begin_SHmakeHead('SRT1', 'SRT2', 'Dummy', self.SHmheadCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHmheadCB(self, a):
		print a
		self.SH_headmade = True

	def SH_writeSpectrum(self):
		statusIC = 0
		ic = None
		self.SH_spectrumWritten = False
		try:
			print "Writing spectrum to file"
			self.ARI_controllers['SH'].begin_SHwriteSpectrum(self.SHspWCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHspWCB(self, a):
		print a
		self.SH_spWritten = True

	def SH_getSpectralPower(self):
		statusIC = 0
		ic = None
		self.SH_powerRead = False
		try:
			print "Getting spectrum power"
			self.ARI_controllers['SH'].begin_SHgetSpectralPower(self.SHspPwCB, self.failureCB)
		except:
			traceback.print_exc()
			self.statusIC = 1

	def SHspPwCB(self, a):
		self.SpectralPower =  a
		self.SH_powerRead = True
		
	def SH_routine(self):
		self.initHound()
		while(not self.SH_initialized):
			time.sleep(0.5)
		self.SH_setBW(self.bw)
		while(not self.SH_bwSetup):
			time.sleep(0.5)
		self.SH_setfc(self.fc)
		while(not self.SH_fcSetup):
			time.sleep(0.5)
		self.SH_setFileName("script_mode.txt")
		while(not self.SH_filenameSetup):
			time.sleep(0.5)
		self.SH_getSpectrum()
		while(not self.SH_readSpectrum):
			time.sleep(0.5)
		self.SH_makeHead()
		while(not self.SH_headmade):
			time.sleep(0.5)
		self.SH_writeSpectrum()
		while(not self.SH_spWritten):
			time.sleep(0.5)
		self.SH_getSpectralPower()
		while(not self.SH_powerRead):
			time.sleep(0.5)
		
	def SHSpectrum_thread(self):
		while(self.getSHsp):
			self.NewSpectrum['SH'] = False 
			self.SH_getSpectrum()
			while(not self.SH_readSpectrum):
				time.sleep(0.5)
			self.NewSpectrum['SH'] = True
			#self.SH_getSpectralPower()
			#while(not self.SH_powerRead):
			#	time.sleep(0.5)
			time.sleep(2)
	
	def ARI_SHSpectrum(self):
		self.observe = True
		obs_Thread = threading.Thread(target = self.SHSpectrum_thread, name='SHSpectrum')
		obs_Thread.start()
		
	def stop_ARI_obs(self):
		self.observe = False
		self.getSHsp = False
		self.stopSRT()
	
	def enableSHspectrum(self):
		self.getSHsp = True
		
	def disableSHspectrum(self):
		self.getSHsp = False
		self.NewSpectrum['SH'] = False



# coding: utf-8
import sys, traceback, Ice
import time
import ARIAPI
import SRTClient

class API():
	def __init__(self):
		self.connected = True
		self.obsMode = ['','']
		self.obsModeCreated = False
		self.arraySetup = False
		self.RxArray = [None,None]
		self.observing = False
		self.observation = [None,None]
		self.spectrumEnabled = False
		self.scanMapinProgress = False
		self.stowinProgress = False
		self.offsets = [0.0, 0.0]
		###############
		self.radecSources = []
		self.planets = []
		self.stars = []
		self.spectrum = {}
		self.obsModeState = {}
	
	def connect(self, IP):
		""" Connects to Observing Mode server
		IP: is the Observing Mode server IP and port
		example: connect(‘192.168.3.100 -p 10015’)
		"""
		#clcdient connection routine to server
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
			self.ic = Ice.initialize(sys.argv, initData)
			# Create proxy
			#base = ic.stringToProxy("SRTController:default -h 192.168.0.6 -p 10000")
			IP_string = "ARIAPI:default -h " + IP
			base = self.ic.stringToProxy(IP_string)
			self.controller = ARIAPI.APIPrx.checkedCast(base)
			self.controller.begin_testConn("connected to observing mode server", self.connectCB, self.failureCB);
			print "Connecting to ARIAPI"
			#self.controller.begin_serverState(self.serverCB, self.failureCB);
			if not self.controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			self.statusIC = 1
			sys.exit(statusIC)
		return
		
	def connectCB(self, a):
		""" connect method Ice callback - 
		Asserts connected state 
		"""
		print a
		self.connected = True

	def disconnect(self):
		""" closes connection to Observing mode server - 
		"""
		#disconnection routine
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Disconnecting.."
		if self.ic:
			try:
				self.ic.destroy()
				self.connected = False
			except:
				traceback.print_exc()
				self.statusIC = 1
				sys.exit(status)
		return
		
	def failureCB(self, ex):
		""" Ice callback when Ice call fails - 
		"""
		#failure Callback
		print "Exception is: " + str(ex)
		return
		
	def genericCB(self, a):
		""" generic functionIce callback - 
		"""
		print a
		return
		
	def setObservingMode(self, mode, instrument):
		""" defines observing mode for observation
		mode : type:(string)  
		        values: ‘SD’ for Single Dish,
		                ‘ARI’ for Interferometer
		instrument: type:(string)
		            values: ‘SRT1’, ‘SRT2’, ‘Double‘ for Single Dish
		                     SH’, ‘ROACH’ for interferometer
		example: setObservingMode(‘SD’,’SRT1’)
		         setObservingMode(‘SD’,Double’)
		         setObservingMode(‘ARI’,’SH’)
		Note that SH is for SignalHound
		SignalHound and ROACH are only considered for ARI mode
		"""
		statusIC = 0
		ic = None
		self.obsMode = ['','']
		try:
			self.controller.begin_setObservingMode(mode, instrument, self.setObsModeCB, self.failureCB);
			print "Setting observing mode"
			self.obsMode = [mode, instrument]
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	def setObsModeCB(self, a):
		""" setObservingMode Ice callback - 
		"""
		print a
		return
		
	def createObservingMode(self):
		""" creates the observing mode in the Observing mode server
		This method sets the connections to the telescope hardware clients- 
		"""
		statusIC = 0
		ic = None
		self.obsModeCreated
		try:
			self.controller.begin_createObservingMode(self.createObsModeCB, self.failureCB);
			print "Setting observing mode"
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	def createObsModeCB(self, a):
		""" createObservingMode Ice callback - 
		asserts obsModeCreated state
		""" 
		print a
		self.obsModeCreated = True
		return
		
	def setupArray(self):
		""" commands array setup and initialization
		Set serial ports on Raspberry pi controllers
		Load parameter file for SRT antennaes
		Initializes SRT antenaes sending them to Stow position
		"""
		statusIC = 0
		ic = None
		self.arraySetup = False
		try:
			self.controller.begin_setupArray(self.setupCB, self.failureCB);
			print "Initializing Array"
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	def setupCB(self, a):
		""" setupArray Ice callback - 
		asserts arraySetup state
		"""
		print a
		self.arraySetup = True
		return
		
	def setRxArray(self,freq, rxmode):
		""" Sets array SRT receiver (does not includes Signal hound yet) - 
		freq: type: (float), the SRT receiver frequency in MHz
		      values: Range to be determined but typical use around 1420.4 MHz
		mode: type: (int), the SRT receiver mode as documented in the SRT manual
		      values:
		'0':{'nfreq':500, 'freqsep':0.04, 'intg':0.1},
		'1':{'nfreq':64, 'freqsep':0.0078125, 'intg':0.1},
		'2':{'nfreq':64, 'freqsep':0.00390625, 'intg':1.04976},
		'3':{'nfreq':64, 'freqsep':0.001953125, 'intg':2.09952},
		'4':{'nfreq':156,'freqsep':0.0078125, 'intg':0.52488},
		'5':{'nfreq':40,'freqsep':1.0, 'intg':0.52488}
		"""
		statusIC = 0
		ic = None
		self.RxArray = [None,None]
		try:
			self.controller.begin_setRxArray(freq, rxmode, self.setRxArrayCB, self.failureCB);
			print "Setting Rx"
			self.RxArray = [freq, rxmode]
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	def setRxArrayCB(self, a):
		""" setRxArray Ice callback - 
		"""
		print a
		return
	
	def observeWithArray(self, mode, target):
		""" Starts observation with Array - 
		mode: type(string) 
		      values: ‘GoTo’ for sending the array to a specific (az,el) position
		            ‘Track’ to command the array to track a source
		target: type (list or string)
		        values: [az, el] is a list defining the target position in (az,el) coordinates\
		                        az and el are floats.
		                Source is a string representing the name of the source
		example: observeWithArray(‘GoTo’,[30,45]) - sends the array to position (30,45)
		         observeWithArray(‘Track’, ‘SgrA’) -- send the array to track SgrA
		"""
		statusIC = 0
		ic = None
		if self.observing:
			print "Observation already started, stop observation before"
			return
		else:
			self.observing = True
			self.observation = [None,None]
		try:
			self.controller.begin_observeWithArray(mode, str(target), self.obswArrayCB, self.failureCB);
			print "Commanding array"
			self.observation = [mode, target]
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def obswArrayCB(self, a):
		""" observeWithArray Ice callback - 
		asserts arraySetup state
		"""
		print a
		return
	
	def stopArray(self):
		""" Stops current array observation
		This function must be called before trying to change the current observation
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_stopArray(self.stopCB, self.failureCB);
			print "Stopping Array"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def stopCB(self, a):
		""" stopArray Ice callback - 
		clears observing state
		"""
		print a
		self.observing = False
		return
	
	def enableSpectrumArray(self):
		""" enables spectrum reading from SRT receivers
		spectrum reading will automatically starts, a reading is received approximately 
		every 3 seconds
		spectrum readings are not received while the antenna is slewing
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_enableSpectrumArray(self.enSpecCB, self.failureCB);
			print "Enabling spectrum reading for array"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def enSpecCB(self, a):
		""" enableSpectrumArray Ice callback - 
		asserts spectrumEnabled state
		"""
		print a
		self.spectrumEnabled = True
		return
	
	def disableSpectrumArray(self):
		""" disables spectrum readings from SRT receivers
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_disableSpectrumArray(self.disSpecCB, self.failureCB);
			print "disabling spectrum reading for array"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def disSpecCB(self, a):
		""" disableSpectrumArray Ice callback - 
		clears spectrumEnabled state
		"""
		print a
		self.spectrumEnabled = False
		return
	
	
	def getLastSpectrumArray(self):
		""" get last spectrum reading from array receivers
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_getLastSpectrum(self.lastSpecCB, self.failureCB);
			print "disabling spectrum reading for array"
		except:
			traceback.print_exc()
			self.statusIC = 1

	def lastSpecCB(self, a):
		""" getLastSpectrumArray Ice callback - 
		obtains the spectrum data
		"""
		print "last spectrum obtained"
		self.spectrum = a
		return
		
	def npointScanMap(self, points, delta, spectrum):
		""" Stars n-point scan map around a target
		points: type (int): the number of points to scan in a single dimension, 
		                    for symmetry this number needs to be odd. In case an even 
		                    number is received it will be approximated to the next odd number
		delta: type (float): the angular space between points of the map. It is not recommended,
		                     it is recommended to not use values < 1.5 degrees
		spectrum: type (bool): Enable the reading of spectrum from SRT receivers for the map, this is
		                      to allow the use of ScanMap with SignalHound.
		Once started it is not possible to interrupt the Scan Map and the antenna status is not updated 
		until the scan ends.
		example: npointScanMap(3, 2, True) , 3x3 scan map with 2 degress separation
		between samplepoints equivalent to offsets of (-2,0,2).
		"""
		statusIC = 0
		ic = None
		if self.scanMapinProgress:
			print "scan map is in progress, wait until complete"
			return
		else:
			self.scanMapinProgress = True
		try:
			self.controller.begin_npointScanMap(points, delta, spectrum, self.scanMapCB, self.failureCB)
			print "Performing Scan Map"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def scanMapCB(self, a):
		""" npointScanMap Ice callback - 
		clears scanMapinProgress state
		"""
		print a
		self.scanMapinProgress = False
		return
	
	def findRadecSources(self):
		""" return a list of observable sources with (Ra, Dec) coordinates
		The catalog of (Ra,Dec) sources is the used by the original SRT software
		An observable source is defined for those with elevation > 15 degrees
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_findRaDecSources(self.fradecCB, self.failureCB);
			print "Getting sources"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def fradecCB(self, a):
		""" findRadecSources Ice callback - 
		"""
		for obj in a:
			print str(obj.source)+" az:"+ str(obj.az) + " el:" + str(obj.el)
		self.radecSources = a
		return a
	
	def findPlanets(self):
		""" Return a list of observable planets as defined by pyEphem library - 
		An observable source is defined for those with elevation > 15 degrees
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_findPlanets(self.fPlanetsCB, self.failureCB);
			print "Getting planets"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def fPlanetsCB(self, a):
		""" findPlanets Ice callback - 
		"""
		for obj in a:
			print str(obj.source)+" az:"+ str(obj.az) + " el:" + str(obj.el)
		self.planets = a

	
	def findStars(self):
		"""
		Return a list of observable stars as defined by pyEphem library - 
		An observable source is defined for those with elevation > 15 degrees
	"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_findStars(self.fStarsCB, self.failureCB);
			print "Getting Stars"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def fStarsCB(self, a):
		""" findStars Ice callback - 
		"""
		for obj in a:
			print str(obj.source)+" az:"+ str(obj.az) + " el:" + str(obj.el)
		self.stars = a

	
	def stowArray(self):
		""" Send array antennae to Stow position
		This command cannot be interrupted and antenna status is not updated during execution- 
		"""
		statusIC = 0
		ic = None
		if self.stowinProgress:
			print "Stow in progress, wait until complete"
			return
		else:
			self.stowinProgress = True
		try:
			self.controller.begin_stowArray(self.stowCB, self.failureCB);
			print "Sending array to stow"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def stowCB(self, a):
		""" stow Ice callback - 
		clears stopinProgress state
		"""
		print a
		self.stowinProgress = False
		return
	
	def setOffsetPointing(self, azoff, eloff):
		""" Sets offset pointing for SRT antennas, antennas will be pointed with the offset
		defined by azoff in azimuth and eloff in elevation.
		azoff: type (float)
		eloff: type (float)
		example: setOffsetPointing( 2, -1.5) 
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_setOffsetPointing(azoff, eloff, self.azoffCB, self.failureCB);
			print "Setting offset pointing"
			self.offsets = [azoff, eloff]
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def azoffCB(self, a):
		""" setOffsetPoint Ice callback - 
		"""
		print a
		return
	
	def getObsModeStatus(self):
		""" Request for Observing Mode Server status 
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_getObsModeState(self.getObsModeStateCB, self.failureCB);
			print "Getting observing mode state"
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def getObsModeStateCB(self, a):
		""" getObsModeStatus Ice callback - 
		returns a list with Observing Mode Server status parameters
		"""
		self.obsModeState = a
		return
	
	def getArrayStatus(self):
		""" Request the status of the SRT antennas
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_getArrayState(self.getArrayStateCB, self.failureCB);
			print "Getting Array Status"
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def getArrayStateCB(self, a):
		""" getArrayStatus Ice callback - 
		Returns a list of status parameters of SRT antennae
		"""
		print a
		return
	
	def apiStatus(self):
		"""Shows the status of the local state variables in the API - 
		"""
		print "Connected: "+ str(self.connected)
		print "Observing Mode: "+ str(self.obsMode)
		print "Observing Mode Created: "+ str(self.obsModeCreated)
		print "Array Setup(Initialized): "+ str(self.arraySetup)
		print "Array Receiver setup: "+ str(self.RxArray)
		print "Observation with array in progress: "+ str(self.observing)
		print "Observation: " + str(self.observation)
		print "Spectrum reading enabled: "+ str(self.spectrumEnabled)
		print "ScanMap in progress: "+ str(self.scanMapinProgress)
		print "Array to Stow in progress: "+ str(self.stowinProgress)
		print "Pointing Offsets: "+ str(self.offsets)
	
###################### Unstable Functions #########################
	
	def setRxSwMode(self, node, mode):
		""" Changes the Receiver switch mode in the SRT antennae for use as SRT receiver or 
		for SignalHound interferometer.This function allow hybrid observations for ARI and SRT
		receivers (This method needs further work for proper integration) Engineering use.
		node: type (string) values: ‘SRT1’, ‘SRT2’- 
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_setRxSwMode(node, mode, self.setRxSwModeCB, self.failureCB);
			print "Setting Rx"
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def setRxSwModeCB(self, a):
		""" setRxSwM0de Ice callback - 
		"""
		print a
		return
	
	def clientShutdown(self):
		"""Stops threads in the client to the HW servers and disconnects the client
		For troubleshooting (needs better control)- 
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_clientShutdown(self.clientSDCB, self.failureCB);
			print "Shutting down ARI Client"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def clientSDCB(self, a):
		""" clientShutdown Ice callback - 
		"""
		print a
		return
	
	def obsModeShutdown(self):
		""" Stop threads and disconnect the OBserving mode server to the clients
		For troubleshooting (needs better control)-
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_obsModeShutdown(self.obsModeSDCB, self.failureCB);
			print "Shutting down obsMode server"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def obsModeSDCB(self, a):
		""" obsModeShutdown Ice callback - 
		"""
		print a
		return
	
	def stopGoingToTarget(self):
		""" stops the array to slew to the commanded target-
		Needs better control
		"""
		statusIC = 0
		ic = None
		try:
			self.controller.begin_stopGoingToTarget(self.stopTargetCB, self.failureCB);
			print "Stopping array"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def stopTargetCB(self, a):
		""" stopGoingToTarget Ice callback - 
		"""
		print a
		return
	
	
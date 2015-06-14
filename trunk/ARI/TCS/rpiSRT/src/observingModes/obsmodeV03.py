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
		self.initialized = False
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

	def setupCB(self, a):
		#generic callback
		print a
		print "Setup finished"
		self.initialized = True
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
			
	def modeCB(self, a):
		print a
	

	def setup(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_setup(self.setupCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" initializing antenna " + node
		except:
			traceback.print_exc()
			self.statusIC = 1

	def trackSource(self, target):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_trackSource(target, self.trackCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" moving antenna" + node + " to target"
			self.tracking
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	
	def trackCB(self, a):
		print a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Antenna on source"
		self.OnSource
		#call by getSpectrum
		if self.mode == 'ARI':
			self.stopSpectrum()
	
	def stopTrack(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				if node.startswith('SRT'):
					self.ARI_controllers[node].begin_stopTrack(self.stopTrackCB, self.failureCB);
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Stopping Antenna " + node
		except:
			traceback.print_exc()
			self.statusIC = 1
	
	def stopTrackCB(self, a):
		print a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" Antenna Stopped"
		
	def getSpectrum(self):
		while(self.readSpectrum):
			statusIC = 0
			ic = None
			try:
				for node in self.nodes:
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
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+sp.sampleStamp.name + " Spectrum Obtained"
		self.spectrum[sp.sampleStamp.name] = self.spec
		self.waitSpectrum = False
		return
		
	def enableSpectrum(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				self.readSpectrum = True
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" starting spectrum reading"
				self.ARI_controllers[node].begin_startSpectrum(self.stopspCB, self.failureCB)
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" starting spectrum reading thread"
			getSpec_thread = threading.Thread(target = self.getSpectrum, name = 'getSpecLoop')
			getSpec_thread.start()

		except:
			traceback.print_exc()
			self.statusIC = 1

	def disableSpectrum(self):
		statusIC = 0
		ic = None
		try:
			for node in self.nodes:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" stopping spectrum reading"
				self.ARI_controllers[node].begin_stopSpectrum(self.stopspCB, self.failureCB)
				self.readSpectrum = False
		except:
			traceback.print_exc()
			self.statusIC = 1

	def stopspCB(self, a):
		print a
		return


class SRTSingleDish(ObsBase):
	def __init__(self, antenna):
		ObsBase.__init__(self)
		self.nodes = [antenna]
		self.observingMode = 'SRT Single Dish: ' + str(self.nodes)
		self.mode = 'SD'
		
	def radioSetup(self, freq, rec_mode):
		statusIC = 0
		ic = None
		try:
			self.new_freq = freq
			self.new_rec_mode = str(rec_mode)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + str(self.nodes)+" "+ setting receiver
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
		return
		
	def status(self):
		statusList = [self.initialized, self.radio_config, self.freq, self.rec_mode, self.new_freq, self.new_rec_mode, self.tracking,self.OnSource]
		return statusList
	
class SRTDoubleSingleDish(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		self.nodes = ['SRT1', 'SRT2']
		self.observingMode = 'SRT Double Single Dish: ' + str(self.nodes)
		self.mode = 'SD'
	
	def radioSetup(self, freq, rec_mode):
		statusIC = 0
		ic = None
		try:
			self.new_freq = freq
			self.new_rec_mode = rec_mode
			for node in self.nodes:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+ " "+node+" "+setting receiver "
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

		
	def status(self):
		statusList = [self.initialized, self.radio_config, self.freq, self.rec_mode, self.new_freq, self.new_rec_mode, self.tracking,self.OnSource]
		return statusList

	
class ARI_SignalHound(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		#self.nodes =['SH']
		self.mode = 'ARI'
		self.nodes =['SRT1', 'SRT2', 'SH']
		self.observingMode = 'ARI Signal Hound: ' + str(self.nodes)
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
			self.ARI_controllers['SH'].begin_SHsetFileName(self.filename, self.SHfilenameCB, self.failureCB)
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
		print a
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
		
	def observation_thread(self, source, freq, bw):
		self.trackSource(source)
		while(self.observe):
			while(self.getSHsp):
				self.SH_getSpectrum()
				while(not self.SH_readSpectrum):
					time.sleep(0.5)
				self.SH_getSpectralPower()
				while(not self.SH_powerRead):
					time.sleep(0.5)
	
	def observation(self, source, freq, bw):
		obs_Thread = threading.Thread(target = self.observation_thread, args=(source, freq, bw), name='observation')
		obs_Thread.start()

class ARI_ROACH(ObsBase):
	def __init__(self):
		ObsBase.__init__(self)
		self.nodes =['SRT1', 'SRT2', 'ROACH']
		self.observingMode = 'ARI ROACH' + str(self.nodes)



	
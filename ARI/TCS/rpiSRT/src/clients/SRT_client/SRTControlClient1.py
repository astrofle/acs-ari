import sys, traceback, Ice
import SRTControl
import ephem
import math
import time
import threading
from time import gmtime, strftime
strftime("%Y-%m-%d %H:%M:%S", gmtime())
import sites
#global variables
#global statusICIC
#global ic
#global controller


#ic = None


class SRT():
	def __init__(self):
		self.IP = '192.168.0.6 -p 1000'
		self.IP_string = "SRTController:default -h " + self.IP
		self.az = 0.0
		self.el = 0.0
		self.aznow = 0.0
		self.elnow = 0.0
		self.axis = 0
		self.tostow = 0
		self.elatstow = 0
		self.azatstow = 0
		self.slew = 0
		self.serialport = ''
		self.lastSRTCom = ''
		self.lastSerialMsg = ''
		self.IsMoving = False
		self.track = False
		self.OnSource = False
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars
		self.target = None
		print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		self.spectrum = []
		self.ic = None
		return 

	def setIP(self, IP):
		self.IP = IP
		self.IP_string = "SRTController:default -h " + self.IP
		return
		
	def find_planets(self):
		self.planets = sites.find_planets(sites.planet_list, self.site)
		print str(len(self.planets))+ " observabable planets: " + str(self.planets)
		
	def find_stars(self):
		self.stars = sites.find_stars(sites.star_list, self.site)
		print str(len(self.stars)) + " observabable stars: " + str(self.stars)
	
	def getStatusCB(self, state):
		#status callback
		self.az = state.az
		self.el = state.el
		self.aznow = state.aznow
		self.elnow = state.elnow
		self.axis = state.axis
		self.tostow = state.tostow
		self.elatstow = state.elatstow
		self.azatstow = state.azatstow
		self.slew = state.slew
		self.serialport = state.serialport
		self.lastSRTCom = state.lastSRTCom
		self.lastSerialMsg = state.lastSerialMsg
		print "SRT antenna Status " + strftime("%Y-%m-%d %H:%M:%S", gmtime())
		print "Commanded azimuth: " + str(self.az)
		print "Commanded elevation: " + str(self.el)
		print "Actual azimuth: " + str(self.aznow)
		print "Actual Elevation: " + str(self.elnow)
		print "Slewing antenna: " + str(self.slew)
		print "Next axis to move: " + str(self.axis)
		print "Commanded to stow: " + str(self.tostow)
		print "elevation axis at stow: " + str(self.elatstow)
		print "azimuth axis at stow position: " + str(self.azatstow)
		print "Controller Serial Port: " + str(self.serialport)
		print "last SRT command: " + str(self.lastSRTCom)
		print "last SRT received message: " + str(self.lastSerialMsg)	
		print "\n"
		return

	def getTrackingStatus(self):
		print "Antenna slewing: " + str(self.IsMoving)
		print "Antenna tracking: " + str(self.track)
		print "Antenna On source: " + str(self.OnSource)


	def getSpectrumCB(self, spect):
		self.spectrum = spect
		print "spectrum received"
		return
	
	def docalCB(self, calcons):
		self.calcons = calcons
		return "calibration done"

	def status(self):
		#asynchronous status
		self.statusIC = 0
		self.ic = None
		try:
			self.controller.begin_SRTStatus(self.getStatusCB, self.failureCB);
			print "getting SRT status"
		except:
			traceback.print_exc()
			self.status = 1
		
	def failureCB(self, ex):
		#failure Callback
		print "Exception is: " + str(ex)
		return
		
	def genericCB(self, a):
		#generic callback
			print a

	def getNameCB(self, a):
			print a

	def serverCB(self, a):
		#generic callback
			state = a.split(',')
			serialPort = state[0].replace('[','')
			antennaInit = state[1].replace(']','')
			if (serialPort != 'None') & (antennaInit != ' False'):
				print "SRT has been initialised in a previus session"
			else:
				print "Proceed with SRT initialization"
			
			print "Serial Port: " + str(serialPort)
			print "Antenna Initialised (sent to stow): " + str(antennaInit)
			
	def connect(self):
		#client connection routine to server
		#global statusIC
		#global ic
		#global controller
		self.statusIC = 0
		try:
			# Reading configuration info
			#configPath = os.environ.get("SWROOT")
			#configPath = configPath + "/config/LCU-config"
			initData = Ice.InitializationData()
			initData.properties = Ice.createProperties()
			initData.properties.load('IceConfig')
			self.ic = Ice.initialize(sys.argv, initData)
			# Create proxy
			#base = ic.stringToProxy("SRTController:default -h 192.168.0.6 -p 10000")
			base = self.ic.stringToProxy(self.IP_string)
			self.controller = SRTControl.telescopePrx.checkedCast(base)
			self.controller.begin_message("connected to controller", self.genericCB, self.failureCB);
			print "Connecting to SRTController"
			self.controller.begin_serverState(self.serverCB, self.failureCB);
			if not self.controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			self.statusIC = 1
			sys.exit(self.statusIC)
		return

	def disconnect(self):
		#disconnection routine
		print "Disconnecting.."
		if self.ic:
			try:
				self.ic.destroy()
			except:
				traceback.print_exc()
				self.statusIC = 1
				sys.exit(status)
		return

	def GetSerialPorts(self):
		#obtain available USB ports with USB-RS232 converters at Raspberry Pi  SRT controller
		self.statusIC = 0
		self.ic = None
		try:
			self.controller.begin_SRTGetSerialPorts(self.genericCB, self.failureCB);
			print "Obtaining available serial ports"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
	
	def SetSerialPort(self, port):
		#sets USB port at Raspberry Pi to control the SRT hardware, this port must match
		#the physical configuration for the R-Pi SRT connection.
		self.statusIC = 0
		self.ic = None
		try:
			self.controller.begin_SRTSetSerialPort(port, self.genericCB, self.failureCB);
			print "Setting serial port"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
	
	def Init(self, parameters):
		#Loads parameters file in the Raspberry Pi SRT controller
		#and send the SRT antenna to stow position as system initialization
		#encoders and position coordinates are initialised.
		#This routine is mandatory when the system is started
		self.statusIC = 0
		self.ic = None
		try:
			self.controller.begin_SRTinit(parameters, self.genericCB, self.failureCB);
			print "loading parameters file and sending antenna to stow"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
			
	def Stow(self):
		#commands SRT antenna to stow position
		self.statusIC = 0
		self.ic = None
		try:
			self.controller.begin_SRTStow(self.genericCB, self.failureCB);
			print "sending antenna to stow"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return

	def AzEl(self, az, el):
		#Command antenna position to (az, el) coordinates	
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTAzEl(az, el, self.genericCB, self.failureCB);
			print "moving the antenna "
			print "commanded coordinates: " + "Azimuth: "+ str(az) + " Elevation: " + str(el)
			self.IsMoving = True
			self.movingThread()
		except:
			traceback.print_exc()
			self.statusIC = 1
		return target
		
	def SetFreq(self, freq, receiver):
		#Sets receiver central frequency and receiver mode (0 to 5)
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTSetFreq(freq, receiver, self.genericCB, self.failureCB);
			print "seting frequency"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
		
	def GetSpectrum(self):
		#Gets spectrum from receiver
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTGetSpectrum(self.getSpectrumCB, self.failureCB)
			print "getting spectrum"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
			
	def threadCB(self, a):
		idx = a.find('AzEl')
		if idx==-1:
			print "Movement finished!!"
			self.IsMoving = False

	def getSRTThreads(self):
		#Get active threads from SRT	
		self.statusIC = 0
		self.ic = None
		try:
			while(self.IsMoving):
				target = self.controller.begin_SRTThreads(self.threadCB, self.failureCB);
				time.sleep(1.0)
		except:
			traceback.print_exc()
			self.statusIC = 1
		return target
		
	def movingThread(self):
		moving_Thread = threading.Thread(target = self.getSRTThreads, name='moving')
		moving_Thread.start()

	
	def track_source(self, source):
		if self.planets.has_key(source):
			source = self.planets[source]
		elif self.stars.has_key(source):
			source = self.stars[source]
		else:
			print "Object not found or not observable"
			return
		self.track = True
		self.OnSource = False
		toSource = 0
		while(self.track):
			toSource = toSource + 1
			if toSource == 2:
				self.OnSource = True
				toSource = 1
			[az, el] = sites.source_azel(source, self.site)
			self.target = self.AzEl(az, el)
			while(self.IsMoving==True):
				time.sleep(10)
		return 
		
	def tracking(self, source):
		tracking_Thread = threading.Thread(target = self.track_source, args =(source,), name='tracking')
		tracking_Thread.start()
			
	def do_calibration(self, method):
		#Call for receiver calibration
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTDoCalibration(method, self.docalCB, self.failureCB)
			print "calibrating receiver"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return

	def clean(self):
		if self.ic:
		#clean up
			try:
				self.ic.destroy()
			except:
				traceback.print_exc()
				self.statusIC = 1











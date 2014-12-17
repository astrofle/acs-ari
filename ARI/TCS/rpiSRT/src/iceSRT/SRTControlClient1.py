import sys, traceback, Ice
import SRTControl
import ephem
import math
import time
import threading
from time import gmtime, strftime
strftime("%Y-%m-%d %H:%M:%S", gmtime())
#global variables
global status
global ic
global controller

planets = [ephem.Sun(),ephem.Moon(),ephem.Mercury(),ephem.Venus(),ephem.Mars(),ephem.Jupiter(),ephem.Saturn()]

ic = None


class SRT():
	def __init__(self):
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
		return 
		
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

	def status(self):
		#asynchronous status
		global status
		status = 0
		ic = None
		try:
			controller.begin_SRTStatus(self.getStatusCB, self.failureCB);
			print "getting SRT status"
		except:
			traceback.print_exc()
			status = 1
		
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
		global status
		global ic
		global controller
		status = 0
		try:
			# Reading configuration info
			#configPath = os.environ.get("SWROOT")
			#configPath = configPath + "/config/LCU-config"
			initData = Ice.InitializationData()
			initData.properties = Ice.createProperties()
			initData.properties.load('IceConfig')
			ic = Ice.initialize(sys.argv, initData)
			# Create proxy
			base = ic.stringToProxy("SRTController:default -h 192.168.0.7 -p 10000")
			controller = SRTControl.telescopePrx.checkedCast(base)
			controller.begin_message("connected to controller", self.genericCB, self.failureCB);
			print "Connecting to SRTController"
			controller.begin_serverState(self.serverCB, self.failureCB);
			if not controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			status = 1
			sys.exit(status)
		return

	def disconnect(self):
		#disconnection routine
		global status
		print "Disconnecting.."
		if ic:
			try:
				ic.destroy()
			except:
				traceback.print_exc()
				status = 1
				sys.exit(status)
		return

	def GetSerialPorts(self):
		#obtain available USB ports with USB-RS232 converters at Raspberry Pi  SRT controller
		global status
		status = 0
		ic = None
		try:
			controller.begin_SRTGetSerialPorts(self.genericCB, self.failureCB);
			print "Obtaining available serial ports"
		except:
			traceback.print_exc()
			status = 1
		return
	
	def SetSerialPort(self, port):
		#sets USB port at Raspberry Pi to control the SRT hardware, this port must match
		#the physical configuration for the R-Pi SRT connection.
		global status
		status = 0
		ic = None
		try:
			controller.begin_SRTSetSerialPort(port, self.genericCB, self.failureCB);
			print "Setting serial port"
		except:
			traceback.print_exc()
			status = 1
		return
	
	def Init(self, parameters):
		#Loads parameters file in the Raspberry Pi SRT controller
		#and send the SRT antenna to stow position as system initialization
		#encoders and position coordinates are initialised.
		#This routine is mandatory when the system is started
		global status
		status = 0
		ic = None
		try:
			controller.begin_SRTinit(parameters, self.genericCB, self.failureCB);
			print "loading parameters file and sending antenna to stow"
		except:
			traceback.print_exc()
			status = 1
		return
			
	def Stow(self):
		#commands SRT antenna to stow position
		global status
		status = 0
		ic = None
		try:
			controller.begin_SRTStow(self.genericCB, self.failureCB);
			print "sending antenna to stow"
		except:
			traceback.print_exc()
			status = 1
		return

	def AzEl(self, az, el):
		#Command antenna position to (az, el) coordinates	
		global status
		status = 0
		ic = None
		try:
			target = controller.begin_SRTAzEl(az, el, self.genericCB, self.failureCB);
			print "moving the antenna"
			self.IsMoving = True
			self.movingThread()
		except:
			traceback.print_exc()
			status = 1
		return target
		
	def threadCB(self, a):
		idx = a.find('AzEl')
		if idx==-1:
			print "Movement finished"
			self.IsMoving = False

	def getThreads(self):
		#Command antenna position to (az, el) coordinates	
		global status
		status = 0
		ic = None
		try:
			while(self.IsMoving):
				target = controller.begin_SRTThreads(self.threadCB, self.failureCB);
				time.sleep(1.0)
		except:
			traceback.print_exc()
			status = 1
		return target
		
	def movingThread(self):
		moving_Thread = threading.Thread(target = self.getThreads, name='moving')
		moving_Thread.start()

def set_site():
	# Local coordinates (Calama)
	place = 'calama'
	lat = '-22.5'
	lon = '-68.9'
	elevation = 2277
	site = ephem.Observer()
	site.lon = lon
	site.lat = lat
	site.elevation = elevation
	return site

def source_azel(object, site):
	site.date = ephem.now()
	object.compute(site)
	az = 180*object.az/math.pi
	el = 180*object.alt/math.pi
	return [az, el]


def find_sources(planets, site):
	sources = []
	for planet in planets:
		[az, el] = source_azel(planet, site)
		if el > 8.0:
			sources.append(planets[planets.index(planet)])
	return sources
	
def track_source(source, site):
	track = True
	while(track):
		[az, el] = source_azel(source, site)
		target = SRTAzEl(az, el)
		while(target.isCompleted()==False):
			time.sleep(2)
	return 
	
if ic:
	#clean up
	try:
		ic.destroy()
	except:
		traceback.print_exc()
		status = 1











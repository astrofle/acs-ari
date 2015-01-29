import sys, traceback, Ice
from time import sleep
import SRTControl
import SRT_control_lib_test as SRT
import threading
import os

class SRTControlI(SRTControl.telescope, SRT.Antenna):
	def __init__(self):
		self.serialport = None
		self.antennaInit = False
		self.az = 0.0
		self.el = 0.0
		self.aznow = 0.0
		self.elnow = 0.0
		self.azcount = 0
		self.elcount = 0
		self.azzcount = 0
		self.ellcount = 0
		self.axis = 0
		self.tostow = 0
		self.azatstow = 0
		self.elatstow = 0
		self.slew = 0
		self.port = None
		self.lastSerialMsg = ''
		self.lastSRTCom = ''
		
	def message(self, s, current = None):
		print s
		return s

	def SRTGetSerialPorts(self, current=None):
		#this function lists the /dev directory and looks for devices of type ttyUSB
		#the function returns the list with available ttyUSB devices
		try:
			devs = os.listdir('/dev/')
			matching = [s for s in devs if "ttyUSB" in s]
			matching.sort()
			return matching
		except Exception, e:
			print str(e)
			return "Failed to gather available serial ports!"
				
	def SRTSetSerialPort(self, s, current = None):
		try:
			print "initializing port "+ s+"\n"
			self.serialport = s
			self.port = self.init_com()
			print "Done!\n"
		except Exception, e:
			print str(e)
			return "Serial port initialization failed!\n"
		return "Serial port initialized!\n"

	def SRTinit(self, s, current = None):
		#print s
		try:
			self.load_parameters(s)
			self.stow_antenna()
			self.antennaInit = True
			return "Done!\n"
		except Exception, e:
			print str(e)
			return "failed to load parameters file or Antenna failed on Stow"
	
	def SRTStow(self, current = None):
		try:
			self.stow_antenna()
			return "Done!\n"
		except Exception, e:
			print str(e)
			return "Failed to Stow antenna"
			
	def SRTStatus(self, current = None):
		_st = self.status(disp = False)
		realStatus = SRTControl.AntennaStatus(az=_st[0], el=_st[1], aznow=_st[2], elnow=_st[3],
		 axis=_st[4], tostow=_st[5], elatstow=_st[6], azatstow=_st[7], slew=_st[8], serialport=_st[9], 
		lastSRTCom=_st[10], lastSerialMsg=_st[11])
		return realStatus

	def SRTAzEl(self, az, el, current = None):
		try:
			self.az = az
			self.el = el
			flip = self.check_flip()
			inLimits = self.get_cmd_inLimits()
			self.azel_thread(az, el)
			return "Commanding antenna movement"
		except Exception, e:
			print str(e)
			return "Failed to move the antenna"
	
	def SRTThreads(self, current = None):
		Threads = threading.enumerate()	
		return str(Threads)
		
	def serverState(self, current = None):
		state = [self.serialport, self.antennaInit]
		return str(state)
		
status = 0
ic = None
try:
	ic = Ice.initialize(sys.argv)
	adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.101 -p 10000")
	object = SRTControlI()
	adapter.add(object, ic.stringToIdentity("SRTController"))
	adapter.activate()
	print "SRT Server up and running!"
	ic.waitForShutdown()
except:
	traceback.print_exc()
	status = 1

if ic:
	#clean up
	try:
		ic.destroy()
	except:
		traceback.print_exc()
		status = 1

sys.exit(status)



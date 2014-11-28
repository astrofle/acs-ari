import sys, traceback, Ice
from time import sleep
import SRTControl
import SRT_control_lib_test as SRT

import os

class SRTControlI(SRTControl.telescope):
	def __init__(self):
		self.A =SRT.Antenna()

	def message(self, s, curren = None):
		print s
		return s

	def SRTGetSerialPorts(self, current=None):
		#this function lists the /dev directory and looks for devices of type ttyUSB
		#the function returns the list with available ttyUSB devices
		devs = os.listdir('/dev/')
		matching = [s for s in devs if "ttyUSB" in s]
		matching.sort()
		return matching
	
	def SRTSetSerialPort(self, s, current = None):
		try:
			print "initializing port "+ s+"\n"
			self.A.serialport = s
			self.A.port = self.A.init_com()
			print "Done!\n"
		except Exception, e:
			print str(e)
			return "Serial port initialization failed!\n"
		return "Serial port initialized!\n"

	def SRTinit(self, s, current = None):
		print s
		self.A.load_parameters(s)
		self.A.stow_antenna()
		return "Done!\n"

	def SRTStow(self, current = None):
		self.A.stow_antenna()
		return "Done!\n"

	def SRTStatus(self, current = None):
		_st = self.A.status(disp = False)
		realStatus = SRTControl.AntennaStatus(az=_st[0], el=_st[1], aznow=_st[2], elnow=_st[3], axis=_st[4], tostow=_st[5], elatstow=_st[6], azatstow=_st[7], slew=_st[8], serialport=_st[9], lastSRTCom=_st[10], lastSerialMsg=_st[11])
		return realStatus

	def SRTAzEl(self, az, el, current = None):
		self.A.azel_thread(az, el)
		return "target"

status = 0
ic = None
try:
	ic = Ice.initialize(sys.argv)
	adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.7 -p 10000")
	object = SRTControlI()
	adapter.add(object, ic.stringToIdentity("SRTController"))
	adapter.activate()
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



import sys, traceback, Ice
import SHControl
import ephem
import math
import time
import threading
from time import gmtime, strftime
strftime("%Y-%m-%d %H:%M:%S", gmtime())
import sites
#global variables
global status
global ic
global controller


ic = None

class SH():
	def __init__(self):
		self.IP = '192.168.0.6 -p 1002'
		self.IP_string = "SHController:default -h " + self.IP
		pass
	
	def setIP(self, IP):
		self.IP = IP
		self.IP_string = "SHController:default -h " + self.IP
		return
	
	def failureCB(self, ex):
		#failure Callback
		print "Exception is: " + str(ex)
		return
		
	def genericCB(self, a):
		#generic callback
		print a
		return
	
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
			#base = ic.stringToProxy("SHController:default -h 192.168.0.6 -p 10002")
			base = ic.stringToProxy(self.IP_string)
			controller = SHControl.SignalHoundPrx.checkedCast(base)
			controller.begin_message("connected to controller", self.genericCB, self.failureCB);
			print "Connecting to SHController"
			#controller.begin_serverState(self.serverCB, self.failureCB);
			if not controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			status = 1
			sys.exit(status)
		return
		
	def Message(self, msg):
		#Gets spectrum from receiver
		global status
		status = 0
		ic = None
		try:
			target = controller.begin_message(msg, self.genericCB, self.failureCB)
			print "sending message"
		except:
			traceback.print_exc()
			status = 1
		return
	
		
if ic:
	#clean up
	try:
		ic.destroy()
	except:
		traceback.print_exc()
		status = 1


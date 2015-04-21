import sys, traceback, Ice
import time
import SRTGUI

class GUI():
	def __init__(self):
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
			IP_string = "SRTGUI:default -h " + IP
			base = ic.stringToProxy(IP_string)
			self.controller = SRTGUI.GUIPrx.checkedCast(base)
			self.controller.begin_testConn("connected to client", self.genericCB, self.failureCB);
			print "Connecting to SRTClient"
			#self.controller.begin_serverState(self.serverCB, self.failureCB);
			if not self.controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			self.statusIC = 1
			sys.exit(statusIC)
		return
		
	def failureCB(self, ex):
		#failure Callback
		print "Exception is: " + str(ex)
		return
		
	def genericCB(self, a):
		#generic callback
		print a
		return	
		
	def SetObservingMode(self, Config, Hw):
		statusIC = 0
		ic = None
		try:
			self.controller.begin_ChooseObservingMode(Config, Hw, self.setObsModeCB, self.failureCB);
			print "Setting observing mode"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def setObsModeCB(self, a):
		print a
		return
		
	def HWConnect(self):
		statusIC = 0
		ic = None
		try:
			self.controller.begin_Connect(self.HWConnectCB, self.failureCB);
			print "Connecting"
		except:
			traceback.print_exc()
			self.statusIC = 1	
			
	def HWConnectCB(self, a):
		print a
		return
		
	def Initialize(self):
		statusIC = 0
		ic = None
		try:
			self.controller.begin_Initialize(self.initCB, self.failureCB);
			print "Initializing Telescope"
		except:
			traceback.print_exc()
			self.statusIC = 1
		
	def initCB(self, a):
		print a
		return
		
	def SetTarget(self, source, freq, rxmode):
		statusIC = 0
		ic = None
		try:
			self.controller.begin_SetTarget(source, freq, rxmode, self.setTargetCB, self.failureCB);
			print "Setting observation"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def setTargetCB(self, a):
		print a
		return
	
	def StartTracking(self):
		statusIC = 0
		ic = None
		try:
			self.controller.begin_StartTracking(self.startCB, self.failureCB);
			print "Starting observation"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def startCB(self, a):
		print a
		return
	
	def StopTracking(self):
		statusIC = 0
		ic = None
		try:
			self.controller.begin_StopTracking(self.stopCB, self.failureCB);
			print "Stopping observation"
		except:
			traceback.print_exc()
			self.statusIC = 1
			
	def stopCB(self, a):
		print a
		return
	
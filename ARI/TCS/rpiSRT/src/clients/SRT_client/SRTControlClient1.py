import sys, traceback, Ice
import SRTControl
import ephem
import math
import time
import threading
from time import gmtime, strftime
strftime("%Y-%m-%d %H:%M:%S", gmtime())
import sites
import matplotlib
#matplotlib.use('QT4Agg')
from pylab import *

#global variables
#global statusICIC
#global ic
#global controller
import numpy as np
import csv 
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
		self.azatstow = 0
		self.slew = 0
		self.serialport = ''
		self.lastSRTCom = ''
		self.lastSerialMsg = ''
		self.IsMoving = False
		self.track = False
		self.toSource = 0
		self.OnSource = False
		self.site = sites.site
		self.planets = sites.planets
		self.stars = sites.stars
		self.SRTsources = sites.SRTsources
		self.target = None
		print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		print str(len(self.SRTsources))+ " observable SRT sources: " + str(self.SRTsources.keys())
		self.spectrum = []
		self.ic = None
		self.getspectrum = True
		self.spectra = False
		self.portInUse = [False, '']
		self.spectrumStarted = False
		self.rGraph = True
		self.statusDisp = False
		self.name = ''
		self.SRTinitialized = False #This variable check if SRT was initialised in a previous session
		self.RxSwitchMode = 'SD'
		########## 
		self.slewing = False
		self.newAzEl = False
		self.cmdstop = False
		self.enSRT = True
		self.enSpec = True
		self.getStatus = True
		self.enObs = True
		self.SRTState = ''
		self.SRTMode = ''
		self.SRTTarget =''
		self.SRTTrack = False
		self.azoffset = 0.0
		self.eloffset = 0.0
		self.azlim1 = None
		self.ellim1 = None
		self.azlim2 = None
		self.ellim2 = None
		self.azcmd = None
		self.elcmd = None
		print "Call shutdown before quiting ipython in order to kill all running threads, in a.o.c. exec ps and kill -9 in the console"

	def find_planets(self):
		self.planets = sites.find_planets(sites.planet_list, self.site)
		print str(len(self.planets))+ " observabable planets: " + str(self.planets)
		
	def find_stars(self):
		self.stars = sites.find_stars(sites.star_list, self.site)
		print str(len(self.stars)) + " observabable stars: " + str(self.stars)
	
	def getTrackingStatus(self):
		print self.name + " Antenna slewing: " + str(self.IsMoving)
		print self.name + " Antenna tracking: " + str(self.track)
		print self.name + " Antenna On source: " + str(self.OnSource)

	####### Ice Callbacks ###################
	def getStatusCB(self, state):
		#status callback
		self.now = state.now
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
		if self.statusDisp:
			print "Antenna name: " + self.name
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
	
	def docalCB(self, calcons):
		#call by do_calibration
		self.calcons = calcons
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " calibration done"
	
	def stowCB(self, a):
		#call by Init and Stow
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Antenna Stowed"
		self.initialized = True # This variable check the SRT initialization in the current session
		self.tostow = 1
		self.IsMoving = False
		self.portInUse[0] = False
		self.status(False)
		self.az = self.aznow
		self.el = self.elnow
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Starting SRT operation loop Thread"
		#self.operSRT()
		self.enSRT = False
		time.sleep(2)
		self.enSRT = True
		operSRT_thread = threading.Thread(target = self.operSRTLoop, name = 'operSRTLoop')
		operSRT_thread.start()
		return
		
	def failureCB(self, ex):
		#failure Callback
		print "Exception is: " + str(ex)
		self.portInUse[0] = False
		return
		
	def genericCB(self, a):
		#generic callback
		print a

	def getNameCB(self, a):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + "connected to " + a
		self.name = a

	def serverCB(self, a):
		#generic callback
		state = a.split(',')
		serialPort = state[0].replace('[','')
		antennaInit = state[1].replace(']','')
		self.aznow = state[2].replace(']','')
		self.elnow = state[3].replace(']','')
		self.az = self.aznow
		self.el = self.elnow
		if (serialPort != 'None') & (antennaInit != ' False'):
			self.SRTinitialized = True
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " SRT has been initialised in a previus session"
			self.getSRTParameters()
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Starting SRT operation loop Thread"
		#self.operSRT()
			self.enSRT = False
			time.sleep(2    )
			self.enSRT = True
			operSRT_thread = threading.Thread(target = self.operSRTLoop, name = 'operSRTLoop')
			operSRT_thread.start()
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Proceed with SRT initialization"
		
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Serial Port: " + str(serialPort)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Antenna Initialised (sent to stow): " + str(antennaInit)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + "Antenna position is: " + str(self.aznow)+", "+str(self.elnow)
	
	def SRTparamCB(self, a):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " with limits: " + a
		self.azlim1 = float(a.split(',')[0])
		self.ellim1 = float(a.split(',')[1])
		self.azlim2 = float(a.split(',')[2])
		self.ellim2 = float(a.split(',')[3])

	######## Control functions #######################
	def setIP(self, IP):
		#set IP before connecting to SRT server
		# format: 'xxx.yyy.z.n -p mmmmm'
		self.IP = IP
		self.IP_string = "SRTController:default -h " + self.IP
		return

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
			#initData.properties.load('IceConfig')
			self.ic = Ice.initialize(sys.argv, initData)
			# Create proxy
			#base = ic.stringToProxy("SRTController:default -h 192.168.0.6 -p 10000")
			base = self.ic.stringToProxy(self.IP_string)
			self.controller = SRTControl.telescopePrx.checkedCast(base)
			self.controller.begin_message("connected to controller", self.genericCB, self.failureCB);
			self.controller.begin_SRTGetName(self.getNameCB, self.failureCB)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +"Connecting to SRTController"
			self.controller.begin_serverState(self.serverCB, self.failureCB);
			Status_Thread = threading.Thread(target = self.status_thread, name='status')
			print "starting status thread"
			Status_Thread.start()
			self.disableSpectrum()
			if not self.controller:
				raise RuntimeError("Invalid proxy")
		except:
			traceback.print_exc()
			self.statusIC = 1
			sys.exit(self.statusIC)
		return

	def disconnect(self):
		#disconnection routine
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" Disconnecting.."
		if self.ic:
			try:
				self.ic.destroy()
			except:
				traceback.print_exc()
				self.statusIC = 1
				sys.exit(status)
		return
	
	def status_thread(self):
		while(self.getStatus):
			self.status(False)
			time.sleep(2)

	def status(self,disp):
		#asynchronous status
		self.statusIC = 0
		self.ic = None
		self.statusDisp = disp
		try:
			self.controller.begin_SRTStatus(self.getStatusCB, self.failureCB);
			#print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " getting status"
		except:
			traceback.print_exc()
			self.status = 1

	def GetSerialPorts(self):
		#obtain available USB ports with USB-RS232 converters at Raspberry Pi  SRT controller
		self.statusIC = 0
		self.ic = None
		try:
			self.controller.begin_SRTGetSerialPorts(self.genericCB, self.failureCB);
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Obtaining available serial ports"
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
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Setting serial port"
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
		if not self.portInUse[0]:
			try:
				self.initialized = False
				self.portInUse = [True, 'Init']
				self.IsMoving = True
				self.controller.begin_SRTinit(parameters, self.stowCB, self.failureCB);
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " loading parameters file and sending antenna to stow"
				self.getSRTParameters()
			except:
				traceback.print_exc()
				self.statusIC = 1
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Wait until initializacion is finished"
		return
		
		
	def Stow(self):
		#commands SRT antenna to stow position
		self.statusIC = 0
		self.ic = None
		if not self.portInUse[0]:
			try:
				self.portInUse = [True, 'Stow']
				self.IsMoving = True
				self.controller.begin_SRTStow(self.stowCB, self.failureCB);
				print  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " sending antenna to stow"
			except:
				traceback.print_exc()
				self.statusIC = 1
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " Wait until stow is finished"
		return
		
	def getSRTParameters(self):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " Obtaining parameters"
		self.controller.begin_SRTgetParameters(self.SRTparamCB, self.failureCB);
	
	#Antenna Movement ##########
	def AzEl(self, az, el):
		#Command antenna position to (az, el) coordinates	
		self.statusIC = 0
		self.ic = None
		target = 0
		if not self.portInUse[0]:
			try:
				self.portInUse = [True, 'AzEl']
				target = self.controller.begin_SRTAzEl(az, el, self.AzEl1CB, self.failureCB);
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " moving the antenna "
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name +  " commanded coordinates: " + "Azimuth: "+ str(az) + " Elevation: " + str(el)
				self.IsMoving = True
				OnTarget_Thread = threading.Thread(target = self.OnTarget_thread, name='OnTarget')
				OnTarget_Thread.start()
			except:
				traceback.print_exc()
				self.statusIC = 1
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " wait until serial port is available or antenna ends movement"
		return target
	
	def OnTarget_thread(self):
		time.sleep(0.2)
		self.slewing = True
		while(self.slewing):
			state = self.controller.SRTOnTarget()
			onTarget = state.split(':')[-1]
			if int(onTarget):
				self.slewing = False
				self.AzElCB("Antenna on Target")
			time.sleep(1)
		
	def AzElCB(self,a):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " "+a
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " Movement finished!!"
		self.IsMoving = False
		self.portInUse[0] = False
		self.status(False)
		if self.SRTMode=='GoTo':
			self.SRTState = 'On target position'
			self.SRTonTarget = True
		if self.SRTMode == 'Track':
			self.toSource = self.toSource + 1
			if self.toSource == 2:
				self.SRTState = 'On target source'
				self.SRTonTarget = True
				self.toSource = 1
				print "Tracking source"
			else:
				self.SRTonTarget = False
		time.sleep(0.2)
		if self.cmdstop:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +"Safe waiting"
			time.sleep(15)
			self.cmdstop = False
			self.SRTonTarget = False
			self.status(False)


	def AzEl1CB(self, a):
		print a
		if (a.split(':')[-1] == '-1'):
			#Antenna command failed
			self.portInUse[0] = False
			self.IsMoving = False
			self.slewing = False
		return
		

	
	# Receiver control	
	def SetFreq(self, freq, receiver):
		#Sets receiver central frequency and receiver mode (0 to 5)
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTSetFreq(freq, str(receiver), self.genericCB, self.failureCB);
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " seting frequency"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return


		
	def SRTGetSpectrum(self):
		#Gets spectrum from receiver
		self.statusIC = 0
		self.ic = None
		#self.spectrumStarted = True
		#while(self.getspectrum):
		if not self.portInUse[0]:
			try:
				#if not self.spectra:
				self.portInUse = [True, 'spectra']
				self.spectra = True
				target = self.controller.begin_SRTGetSpectrum(self.getSpectrumCB, self.failureCB)
			except:
				traceback.print_exc()
				self.statusIC = 1
		#time.sleep(1)
		else:
			if self.IsMoving:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " wait until serial port is available or antenna ends movement"
			else:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " wait until serial port is available or spectrum is acquired"
		return

	def getSpectrumCB(self, spect):
		#call by getSpectrum
		self.spectrum = spect
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " spectrum received"
		self.spectra = False
		self.portInUse[0] = False
		fspec = open('fspec.csv','w')
		fspecW = csv.writer(fspec)
		fspecd = open('fspecd.csv','w')
		fspecdW = csv.writer(fspecd)
		favspec = open('favspec.csv','w')
		favspecW = csv.writer(favspec)
		favspecc = open('favspecc.csv','w')
		favspeccW = csv.writer(favspecc)
		fspecW.writerow(spect.spec)
		fspecdW.writerow(spect.specd)
		favspecW.writerow(spect.avspec)
		favspeccW.writerow(spect.avspecc)
		fspec.close()
		fspecd.close()
		favspec.close()
		favspecc.close()
		#if self.toSource == 1:
		#	self.StopSpectrum()
		time.sleep(1)
		return
		
	######## Thread functions	
		
			
	def do_calibration(self, method):
		#Call for receiver calibration
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTDoCalibration(method, self.docalCB, self.failureCB)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " calibrating receiver"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
		
	def graph_thread(self):
		#plot thread
		graph_thread = threading.Thread(target = self.graph)
		graph_thread.start()

	def graph(self):
		#plot loop
		#the plot routine is intented to maximize plot speed
		#idea from 
		plot(self.spectrum.spec)
		show(block=False)
		while(self.rGraph):
			plot(self.spectrum.spec)
			show(block=False)
			time.sleep(2)

	def initGraph(self):
		self.fig, self.ax = plt.subplots()
		self.line, = self.ax.plot(np.zeros(256))
		self.ax.set_autoscale_on(False)
		self.line.set_xdata(range(256))
		#self.ax.set_yscale('log')
		plt.grid(True)
		plt.show(block=False)

	def clear(self):
		#Call for receiver calibration
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTClear(self.genericCB, self.failureCB)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " clearing spectrum"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return

	def clean(self):
		if self.ic:
		#clean up#
			try:
				self.ic.destroy()
			except:
				traceback.print_exc()
				self.statusIC = 1
		return

	def getName(self):
		#Call for antenna name
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTGetName(self.getNameCB, self.failureCB)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +"getting antenna name"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
		
	def SetRxMode(self, mode): 
		#Call for antenna name
		self.statusIC = 0
		self.ic = None
		try:
			target = self.controller.begin_SRTsetMode(mode, self.setModeCB, self.failureCB)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +"setting receiver mode"
		except:
			traceback.print_exc()
			self.statusIC = 1
		return
		
	def setModeCB(self, a):
		print a
		self.RxSwitchMode = a
		
	def operSRT(self):
		operSRT_thread = threading.Thread(target = self.operSRTLoop, name = 'operSRTLoop')
		operSRT_thread.start()
	
	def operSRTLoop(self):
		#This is the loop that manages the commands to control the SRT
		while(self.enSRT):
			if self.newAzEl:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " loop newazel"
				#self.stopAzEl()
				while self.portInUse[0]:
					print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " port in use"
					time.sleep(0.5)
				self.AzEl(self.azcmd,self.elcmd)
				self.newAzEl = False
			else:
				while (self.portInUse[0] or self.cmdstop):
					time.sleep(0.5)
				if self.enSpec:
					self.SRTGetSpectrum()
			time.sleep(1)
		
	def enableSRT(self):
		self.enSRT = True
		self.getStatus = True
	
	def disableSRT(self):
		self.enSRT = False
		self.getStatus = False
	
	def setAzEl(self, aznew, elnew):
		self.azcmd = aznew
		self.elcmd = elnew
		self.newAzEl = True
		
	def stopAzEl(self):
		self.slewing = False
		self.cmdstop = True
		self.statusIC = 0
		self.ic = None
		if self.IsMoving:
			try:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +"Stopping antenna by command!"
				self.controller.begin_SRTStopSlew(self.AzElCB, self.failureCB);
			except:
				traceback.print_exc()
				self.statusIC = 1
		
	def disableSpectrum(self):
		self.enSpec = False
	
	def enableSpectrum(self):
		self.enSpec = True
		
	
	def stopObs(self):
		self.SRTTrack = False
		self.enSRT = False
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " Observation Threads stopped"

	def driftObs(self):
		self.SRTTrack = False
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " Track stopped, drift observing"

	def stopGoingToTarget(self):
		self.SRTTrack = False
		self.newAzEl = False
		self.stopAzEl()


	def obswSRT(self, mode, target):
	# mode: 'GoTo' --> target = position
	# mode: 'Track' --> target = 'Source'
		#### SRT starts in STOP state ###
		self.SRTState = 'Idle'
		self.SRTonTarget = False
		self.SRTMode = mode
		if (type(target) == list):
			radec = 0
			obsTarget = ['position',target]
			self.SRTTarget = 'position'
		if (type(target) == str):
			self.SRTTarget = 'Source'
			if self.planets.has_key(target):
				source = self.planets[target]
				radec = 0
			elif self.stars.has_key(target):
				source = self.stars[target]
				radec = 0
			elif self.SRTsources.has_key(target):
				source = self.SRTsources[target]
				radec = 1
			else:
				self.SRTTarget = 'Error'
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " Object not found or not observable"
				self.toSource = -1
				return
			obsTarget = ['source',source]
		obswSRT_thread = threading.Thread(target = self.obswSRTLoop, args = (mode, obsTarget, radec), name = 'obswSRTLoop')
		obswSRT_thread.start()
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " Calling SRT observation thread"
		return

	def obswSRTLoop(self, mode, obsTarget, radec):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " Starting SRT observation thread with "
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " observing with SRT using " + str(obsTarget)
		self.SRTMode = mode
		if mode == 'GoTo':
			self.SRTTrack = False
			self.setAzEl(obsTarget[1][0], obsTarget[1][1])
			self.SRTState = 'Slewing to position'
		if mode == 'Track':
			self.SRTState = 'Slewing to source'
			self.toSource = 0
			self.SRTTrack = True
			while(self.enObs):
				while(self.SRTTrack):
					if radec:
						[az, el] = sites.radec2azel(obsTarget[1]['ra'], obsTarget[1]['dec'], self.site)
					else:
						[az, el] = sites.source_azel(source, self.site)
					#Implementar para traer azlim2 desde parametersV01
					az = az + self.azoffset
					el = el + self.eloffset
					if az > (360 + self.azlim1):
						naz = az - 360
					else:
						naz = az
					if ((abs(naz - float(self.aznow))>0.2) or (abs(el - float(self.elnow))>0.2)):
						print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name + " new tracking position"
						self.SRTState = 'Slewing to source'
						self.setAzEl(az, el)
					time.sleep(10)
				time.sleep(5)

		
	def shutdown(self):
		#Observation loop
		self.SRTTrack = False
		#Operation loop
		self.enSRT = False
		#status loop
		self.getStatus = False
		#disconnect ICe
		self.disconnect()
		
	def state(self):
		print "SRTState: "+ self.SRTState
		print "SRTonTarget: " + self.SRTonTarget
		print "SRTMode: " + self.SRTMode
		print "SRTTarget: " + self.SRTTarget
		print "SRTTrack: "+ self.SRTTrack
		print "enObs: " + self.enObs
		print "newAzEl: " + self.newAzEl
		print "enSRT: " + self.enSRT
		print "enSpec: " + self.enSpec
		print "slewing: " + self.slewing
		print "cmdstop: " + self.cmdstop
		print "InMoving: " + self.IsMoving
		print "getStatus: " + self.getStatus
		print "portInUse: " + self.portInUse
		print "spectra: " + self.spectra
		print "RxSwitchMode: "  + self.RxSwitchMode
		print "toSource: " + self.toSource
		print "SRTinitialized: " + self.SRTinitialized
		print "initialized: " + self.initialized 
		print "toStow: " + self.tostow 




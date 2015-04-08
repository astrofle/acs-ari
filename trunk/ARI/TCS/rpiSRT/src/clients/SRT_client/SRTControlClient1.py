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
		self.SRTsources = sites.SRTsources
		self.target = None
		print str(len(self.planets))+ " observable planets: " + str(self.planets.keys())
		print str(len(self.stars))+ " observable stars: " + str(self.stars.keys())
		print str(len(self.SRTsources))+ " observable SRT sources: " + str(self.SRTsources.keys())
		self.spectrum = []
		self.ic = None
		self.getspectrum = True
		self.spectra = False
		self.portInUse = False
		self.spectrumStarted = False
		self.rGraph = True
		self.statusDisp = False
		return 
		
	def find_planets(self):
		self.planets = sites.find_planets(sites.planet_list, self.site)
		print str(len(self.planets))+ " observabable planets: " + str(self.planets)
		
	def find_stars(self):
		self.stars = sites.find_stars(sites.star_list, self.site)
		print str(len(self.stars)) + " observabable stars: " + str(self.stars)
	
	def getTrackingStatus(self):
		print "Antenna slewing: " + str(self.IsMoving)
		print "Antenna tracking: " + str(self.track)
		print "Antenna On source: " + str(self.OnSource)

	####### Ice Callbacks ###################
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
		if self.statusDisp:
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
		return "calibration done"
	
	def stowCB(self, a):
		#call by Init and Stow
		print "Antenna Stowed"
		self.tostow = 1
		self.IsMoving = False
		self.portInUse = False
		self.status(False)
		return
		
	def failureCB(self, ex):
		#failure Callback
		print "Exception is: " + str(ex)
		self.portInUse = False
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

	def status(self,disp):
		#asynchronous status
		self.statusIC = 0
		self.ic = None
		self.statusDisp = disp
		try:
			self.controller.begin_SRTStatus(self.getStatusCB, self.failureCB);
			print "getting SRT status"
		except:
			traceback.print_exc()
			self.status = 1

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
		if not self.portInUse:
			try:
				self.portInUse = True
				self.IsMoving = True
				self.controller.begin_SRTinit(parameters, self.stowCB, self.failureCB);
				print "loading parameters file and sending antenna to stow"
			except:
				traceback.print_exc()
				self.statusIC = 1
		else:
			print "Wait until initializacion is finished"
		return
		
			
	def Stow(self):
		#commands SRT antenna to stow position
		self.statusIC = 0
		self.ic = None
		if not self.portInUse:
			try:
				self.portInUse = True
				self.IsMoving = True
				self.controller.begin_SRTStow(self.stowCB, self.failureCB);
				print "sending antenna to stow"
			except:
				traceback.print_exc()
				self.statusIC = 1
		else:
			print "Wait until stow is finished"
		return

	#Antenna Movement ##########
	def AzEl(self, az, el):
		#Command antenna position to (az, el) coordinates	
		self.statusIC = 0
		self.ic = None
		target = 0
		if not self.portInUse:		
			try:
				self.portInUse = True
				target = self.controller.begin_SRTAzEl(az, el, self.genericCB, self.failureCB);
				print "moving the antenna "
				print "commanded coordinates: " + "Azimuth: "+ str(az) + " Elevation: " + str(el)
				self.IsMoving = True
				self.movingThread()
			except:
				traceback.print_exc()
				self.statusIC = 1
		else:
			print "wait until serial port is available or antenna end movement"
		return target

	def movingThread(self):
		moving_Thread = threading.Thread(target = self.getSRTThreads, name='moving')
		moving_Thread.start()

	def getSRTThreads(self):
		#Get active threads from SRT	
		self.statusIC = 0
		self.ic = None
		target = 0
		try:
			while(self.IsMoving or self.spectra):
				target = self.controller.begin_SRTThreads(self.threadCB, self.failureCB);
				time.sleep(1.0)
		except:
			traceback.print_exc()
			self.statusIC = 1
		return target

	def threadCB(self, a):
		idx = a.find('AzEl')
		if (self.IsMoving and idx==-1):
			print "Movement finished!!"
			self.IsMoving = False
			self.portInUse = False
			self.status(False)
		idx2 = a.find('spectra')
		if (self.spectra and idx2==-1):
			print "Spectra finished!!"
			self.spectra = False
			self.portInUse = False
	
	# Receiver control	
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

	def StopSpectrum(self):
		self.getspectrum = 0
		self.spectrumStarted = False
	
	
	def GetSpectrum(self):
		target = 0
		self.getspectrum = 1
		if self.spectrumStarted:
			print "this is already started"
			return target
		if (not self.IsMoving):
			target = self.spectraThread()
			print "getting spectrum"
		else:
			print "wait until antenna stop movement"
		return target

	def spectraThread(self):
		spectra_Thread = threading.Thread(target = self.SRTGetSpectrum, name='spectra')
		spectra_Thread.start()
		
	def SRTGetSpectrum(self):
		#Gets spectrum from receiver
		self.statusIC = 0
		self.ic = None
		self.spectrumStarted = True
		while(self.getspectrum):
			if not self.portInUse:
				try:
					if not self.spectra:
						self.portInUse = True
						self.spectra = True
						target = self.controller.begin_SRTGetSpectrum(self.getSpectrumCB, self.failureCB)
				except:
					traceback.print_exc()
					self.statusIC = 1
			time.sleep(1)
		return

	def getSpectrumCB(self, spect):
		#call by getSpectrum
		self.spectrum = spect
		print "spectrum received"
		self.spectra = False
		self.portInUse = False
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
		return
		
	######## Thread functions	
		
	def track_source(self, source): 
		self.GetSpectrum()
		time.sleep(3)
		if self.planets.has_key(source):
			source = self.planets[source]
			radec = 0
		elif self.stars.has_key(source):
			source = self.stars[source]
			radec = 0
		elif self.SRTsources.has_key(source):
			source = self.SRTsources[source]
			radec = 1
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
			if (not self.IsMoving and not self.portInUse):
				if radec:
					[az, el] = sites.radec2azel(source['ra'], source['dec'], self.site)
				else:
					[az, el] = sites.source_azel(source, self.site)
				#Implementar para traer azlim2 desde parametersV01
				if az > 270:
					naz = az - 360
				else:
					naz = az
				if ((abs(naz - self.aznow)>0.2) or (abs(el - self.elnow)>0.2)):
					print naz, self.aznow, el, self.elnow
					self.target = self.AzEl(az, el)
			time.sleep(2)
		return 
		
	def tracking(self, source):
		tracking_Thread = threading.Thread(target = self.track_source, args =(source,), name='tracking')
		tracking_Thread.start()
		
	def StopTrack(self):
		self.track = False
		
	def Stop(self):
		self.StopSpectrum()
		self.StopTrack()
		
			
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
			print "clearing spectrum"
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
		return








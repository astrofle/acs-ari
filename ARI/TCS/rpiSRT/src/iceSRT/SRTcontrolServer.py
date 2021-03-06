import sys, traceback, Ice
from time import sleep
import time
import SRTControl
import SRT_control_lib_test as SRT
import threading
import os
import RPi.GPIO as GPIO

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
		self.OnTarget = False
		#radio parameters
		# Variables for receiver
		self.fcenter = 1420.4 # default for continuum
		self.freqa = 1420.0
		self.restfreq = 1420.406 # se usa para calcular la velocidad en doppler H-Line rest freq

		#If not simulation fcenter = 1420.0, nfreq = 1, freqsep = 0.04, intg = 0.1
		#If simulation fcenter = 1420.4, nfreq = 40
		self.tstart = 0
		self.tsys = 0.0
		self.stopproc = 0
		self.atten = 0
		self.calon = 0
		self.docal = 1
		self.sourn = 0
		self.track = 0
		self.scan = 0
		self.bsw = 0
		self.mancal = 0
		self.sig = 1
		self.specd = [0]*256
		self.spec = [0]*256
		self.avspec = [0]*256
		self.avspecc = [0]*256
		self.avspecs = [0]*256
		self.avspeccs= [0]*256
		self.bswav = 0.0 
		self.bswsq = 0.0
		self.bswlast = 0.0
		self.bswcycles = 0.0
		self.av = 0.0
		self.avc = 0.0
		self.paver = 0.0
		self.prms =0.0
		self.pnum = 1e-60
		self.receiving = False
		self.waitingSp = False
		self.eloff = 0.0
		self.azoff = 0.0
		self.name = os.uname()[1] #Antenna name
		self.sampleStamp = []
		self.SD_ARI_Switch_init()
		self.portInUse = [False, '']
		self.azlim1 = None
		self.azlim2 = None
		self.ellim1 = None
		self.ellim2 = None
		self.azoff1 = 0
		self.eloff1 = 0 
		self.calcons = 1.0


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
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Failed to gather available serial ports!"
				
	def SRTSetSerialPort(self, s, current = None):
		try:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " initializing port "+ s+"\n"
			self.serialport = s
			self.port = self.init_com()
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Done!\n"
		except Exception, e:
			print str(e)
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Serial port initialization failed!\n"
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Serial port initialized!\n"

	def SRTinit(self, s, current = None):
		#print s
		try:
			self.load_parameters(s)
			self.stow_antenna()
			self.antennaInit = True
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Done!\n"
		except Exception, e:
			print str(e)
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " failed to load parameters file or Antenna failed on Stow"
	
	def SRTStow(self, current = None):
		try:
			self.stow_antenna()
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Done!\n"
		except Exception, e:
			print str(e)
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Failed to Stow antenna"
			
	def SRTStatus(self, current = None):
		_st = self.status(disp = False)
		realStatus = SRTControl.AntennaStatus(now=_st[12], name=_st[13] , az=self.az, el=self.el, aznow=self.aznow, elnow=self.elnow,
		 axis=_st[4], tostow=_st[5], elatstow=_st[6], azatstow=_st[7], slew=_st[8], serialport=_st[9], 
		lastSRTCom=_st[10], lastSerialMsg=_st[11])
		return realStatus

	def SRTgetParameters(self, current= None):
		params= str(self.azlim1)+','+str(self.ellim1) + ','+str(self.azlim2)+','+str(self.ellim2)
		return params

	def SRTAzEl(self, az, el, current = None):
		try:
			self.az = az
			self.el = el
			flip = self.check_flip()
			self.normalize_az()
			inLimits = self.get_cmd_inLimits()
			if inLimits:
				self.azel_thread(az+ self.azoff, el+self.azoff)
				return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Commanding antenna movement to ("+str(az)+","+str(el)+") with offset: (" + str(self.azoff1) + "," + str(self.eloff1)+")"
				#print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Commanding antenna movement to ("+str(az)+","+str(el)+") with offset: (" + str(self.azoff) + "," + str(self.eloff)+")"
				#while(not self.OnTarget):
				#	sleep(1)
				#return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Moving antenna to (az,el)"
			else:
				return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Command out of limits!:0"
		except Exception, e:
			print str(e)
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Failed to move the antenna:-1"
	
	def SRTOnTarget(self, current = None):
		if not self.OnTarget:
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Not on target:0"
		else:
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Antenna reached (az,el):1"
			
		
	def SRTStopSlew(self, current = None):
		self.stop_slew()
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " slew stopped"
	
	def SRTThreads(self, current = None):
		Threads = threading.enumerate()	
		return str(Threads)
		
	def serverState(self, current = None):
		state = [self.serialport, self.antennaInit, self.aznow, self.elnow]
		return str(state)
	
	def SRTSetFreq(self, freq, receiver, current = None):
		try:
			self.set_freq(freq, receiver)
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Frequency changed"
		except Exception, e:
			print str(e)
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Failed to change frequency"
	
	def SRTDoCalibration(self, method, current = None):
		try:
			if method == 'vane':
				self.vane_calibration()
			if method == 'noise':
				self.noise_calibration()
			return self.calcons
		except Exception, e:
			print str(e)
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Failed to calibrate"

	def SRTGetSpectrum(self, current = None):
		self.spectra_thread()
		sleep(1)
		#return "obtaining spectrum"
		#_sp = self.spectra()
		while(self.waitingSp):
			sleep(0.5)
		print self.waitingSp
		stamps = SRTControl.stamp(name = self.sampleStamp[0], 
		timdate = self.sampleStamp[1],
		aznow = self.sampleStamp[2],
		elnow = self.sampleStamp[3],
		temperature = self.sampleStamp[4],
		freq0 = self.sampleStamp[5],
		av = self.sampleStamp[6],
		avc = self.sampleStamp[7],
		nfreq = self.sampleStamp[8],
		freqsep = self.sampleStamp[9])
		sp = SRTControl.specs(stamps, self.spec, self.avspecs, self.avspeccs,self.specd)
		return sp
						
	def SRTClear(self, current = None):
		self.clear()
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Clear Done!"

	def SRTSetazeloff(self, azoff, eloff, current = None):
		self.azoff1 = azoff
		self.eloff1 = eloff
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " Corrections updated"
	
	def SRTGetName(self, current = None):
		print "I am " + self.name
		return self.name

	def SRTsetMode(self, mode, current = None):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " setting " + self.name+ "to " + mode
		self.SD_ARI_Switch(mode)
		return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+ self.name + " set to " + mode
	
	def SRTportInUse(self, current = None):
		p = SRTControl.inuse(self.portInUse[0], self.portInUse[1])
		return p
		
try:
	if len(sys.argv)<2:
		print "use SRTcontrolServer.py  -h 192.168.0.6 -p 10000"
		sys.exit()
	IP =  ' '.join(sys.argv[1:])
	IP = "default -h " + IP
except:
	print "use SRTcontrolServer.py default -h 192.168.0.6 -p 10000 or 10001"
		
		
status = 0
ic = None
try:
	#ic = Ice.initialize(sys.argv)
	ic = Ice.initialize([''])
	#adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.6 -p 10000")
	adapter = ic.createObjectAdapterWithEndpoints("SRTController", IP)
	object = SRTControlI()
	adapter.add(object, ic.stringToIdentity("SRTController"))
	adapter.activate()
	print " SRT Server up and running!"
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



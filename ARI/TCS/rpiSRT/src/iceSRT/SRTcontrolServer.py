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
			return self.name + " Failed to gather available serial ports!"
				
	def SRTSetSerialPort(self, s, current = None):
		try:
			print self.name + " initializing port "+ s+"\n"
			self.serialport = s
			self.port = self.init_com()
			print "Done!\n"
		except Exception, e:
			print str(e)
			return self.name + " Serial port initialization failed!\n"
		return self.name + " Serial port initialized!\n"

	def SRTinit(self, s, current = None):
		#print s
		try:
			self.load_parameters(s)
			self.stow_antenna()
			self.antennaInit = True
			return self.name + " Done!\n"
		except Exception, e:
			print str(e)
			return self.name + " failed to load parameters file or Antenna failed on Stow"
	
	def SRTStow(self, current = None):
		try:
			self.stow_antenna()
			return self.name + " Done!\n"
		except Exception, e:
			print str(e)
			return self.name + " Failed to Stow antenna"
			
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
			self.normalize_az()
			inLimits = self.get_cmd_inLimits()
			if inLimits:
				self.azel_thread(az+ self.azoff, el+self.azoff)
				print self.name + "Commanding antenna movement with offset: (" + str(self.azoff) + "," + str(self.eloff)+")"
				while(not self.OnTarget):
					sleep(1)
				return self.name + "Antenna reached (az,el)"
			else:
				return self.name + "Command out of limits!"
		except Exception, e:
			print str(e)
			return self.name + "Failed to move the antenna"
	
	def SRTThreads(self, current = None):
		Threads = threading.enumerate()	
		return str(Threads)
		
	def serverState(self, current = None):
		state = [self.serialport, self.antennaInit]
		return str(state)
	
	def SRTSetFreq(self, freq, receiver, current = None):
		try:
			self.set_freq(freq, receiver)
			return self.name + " Frequency changed"
		except Exception, e:
			print str(e)
			return self.name + " Failed to change frequency"
	
	def SRTDoCalibration(self, method, current = None):
		try:
			if method == 'vane':
				self.vane_calibration()
			if method == 'noise':
				self.noise_calibration()
			return self.calcons
		except Exception, e:
			print str(e)
			return self.name + " Failed to calibrate"

	def SRTGetSpectrum(self, current = None):
		self.spectra_thread()
		#return "obtaining spectrum"
		#_sp = self.spectra()
		while(self.waitingSp):
			sleep(0.2)
		sp = SRTControl.specs(self.sampleStamp, self.specd, self.spec, self.avspecs, self.avspeccs)
		return sp
						
	def SRTClear(self, current = None):
		self.clear()
		return self.name + " Clear Done!"

	def SRTSet_azeloff(self, azoff, eloff):
		self.azoff = azoff
		self.eloff = eloff
		return self.name + " Corrections updated"
	
	def SRTGetName(self, current = None):
		print "I am " + self.name
		return self.name

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



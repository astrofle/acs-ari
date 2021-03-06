#!/usr/bin/env python

#get_cmd_inLimits will terminate the script is (az,el) is out of limits
#It returns a 1 if the command is in limits, this can be used to put an
#interlock and avoid to terminate the script.

#check_flip is implemented for completeness of the code, however is not
#modifying the (az,el) values. This function is for non-cassi mounts.
#check_flip might be called before get_cmd_inLimits. Note that in the
#current Cassi mount pushrod = 1 in the parameters file, thus no change will
#happen to (az,el).

#check_count verifies the integrity of the encoder counts, if the count is corrupted
#the script will be terminated to force antenna reinitializacion with stow.

import sys
import os
import math
import serial
import time
#import parametersV01 as p
import ephem
import importlib
import threading
import struct
import RPi.GPIO as GPIO
global port 
global p

print "importing SRT library"

class Antenna:
	def __init__(self):
		#variables for antenna control
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
		self.serialport = ''
		self.port = None
		self.lastSerialMsg = ''
		self.lastSRTCom = ''
		
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
		self.pnum = 1e-6
		self.receiving = False
		self.waitingSp = False
		self.eloff = 0.0
		self.azoff = 0.0
		#from config file (read *.cat)
		#receiver default initialization from *.cat 
		#(whenever the word digital is present in the cat file)
		#If not present no initialization is done
		self.name = os.uname()[1] #Antenna name
		self.sampleStamp = []
		self.portInUse = [False, '']
		self.azlim1 = None
		self.azlim2 = None
		self.ellim1 = None
		self.ellim2 = None


	def status(self, disp):
		now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
		if(disp == True):
			print "Date: " + now
			print "Antenna: " + self.name
			print "commanded azimuth: " + str(self.az)
			print "commanded elevation: " + str(self.el)
			print "current azimuth: " + str(self.aznow)
			print "current elevation: " + str(self.elnow)
			print "next axis to move: " + str(self.axis)
			print "sent to stow: " + str(self.tostow)
			print "elevation at stow: " + str(self.elatstow)
			print "azimuth at stow: " + str(self.azatstow)
			print "slewing" + str(self.slew)
			print "serial port: " + self.serialport
			print "last SRT command: " + str(self.lastSRTCom)
			print "last received Serial message: " + str(self.lastSerialMsg)
		return self.az, self.el, self.aznow, self.elnow, self.axis, self.tostow, self.elatstow, self.azatstow, self.slew, self.serialport, str(self.lastSRTCom), str(self.lastSerialMsg), now, self.name
		
	def init_com(self):
		#serial port USB-RS232 initializacion
		port1 = '/dev/'+self.serialport
		try:
			ser = serial.Serial(port1, baudrate=2400, timeout = 10)
		except Exception, e:
			print str(e)
		return ser

	def send_command(self, cmd):
		#send command string to SRT HW via USB-RS232
		#print "sending :"+ cmd
		self.port.write(cmd)
		return
		
	def get_serialAnswer(self):
		#reads answer from SRT HW via USB-RS232
		finished = 0;
		cmd_r=''
		timeout = time.time() + 240
		while(finished == 0):
			#print "reading serial port"
			cmd_r = cmd_r + self.port.read(self.port.inWaiting())
			if(cmd_r.find('\r') !=-1):
				finished = 1
			else:
				cmd_r = cmd_r +self.port.read(self.port.inWaiting())
			if time.time() > timeout:
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name +" Serial port time out"
				finished = 1
			time.sleep(1)
	
		#parses received answer
		cmd_r = cmd_r.split(' ')
		#print cmd_r
		self.lastSerialMsg =  [int(time.time()), cmd_r]
		return cmd_r
		
	def sim_serialAnswer(self,mm, count):
		#SRT HW simulated answer for test
		cmd_r = "M "+str(count)+" 0 "+str(mm)+"\r"
		cmd_r = cmd_r.split(' ')
		time.sleep(1)	
		self.lastSerialMsg =  [int(time.time()), cmd_r]
		return cmd_r

	def parseAnswer(self, cmd_r, count):
		#Whenever answer first character is different from M or T then there is a communication failure
		#This function is not used for antenna stow.
		if ((cmd_r[0] !="M") & (cmd_r[0] !="T")):
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + " error, comandar a stow position"
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name + str(cmd_r)
			sys.exit()
		else:
			#print "OK"
			rec_count = float(cmd_r[1]) #encoder count read back from antenna controller
			b2count = float(cmd_r[2]) #read back from antenna controller
		#count is >5000 for stow command, fcount = 2*rec_count = 2*count 
		#and updates the current axis count whit the encoder counts during last step
		if (count < 5000):
			fcount = count * 2 + b2count; # add extra 1/2 count from motor coast
		else:
			fcount = 0;
		return [rec_count, fcount]

	def antenna_positionStatus(self, mm, cmd_r, fcount):
		#Stop position verification
		#condition for entering elevation stow position
		if ((mm == 2) & (cmd_r[0] == 'T') & (self.tostow == 1)):
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+self.name +" elevation at stow position"
			self.elatstow = 1;
			self.elcount = 0
			self.elnow = p.ellim1;
	
		#condition for entering azimuth stow position
		if ((mm == 0) & (cmd_r[0] == 'T') & (self.tostow == 1)):
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+self.name +" azimuth at stow position"
			self.azatstow = 1;
			self.azcount = 0;
			self.aznow= p.azlim1
	
		#Time out from antenna
		if ((cmd_r[0] == 'T') & (self.tostow == 0)):
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" "+self.name +" timeout from antenna, command to stow"
			sys.exit()
	
		#axis current azcount and elcount updated with count variation from last step fcount
		if (cmd_r[0] == 'M'):
			if (self.axis == 0):
				#Azimuth moved
				self.azatstow = 0;
				if (mm == 1):
					self.azcount = self.azcount + fcount;
				else:
					self.azcount = self.azcount - fcount;
			if (self.axis == 1):
				#Elevation moved
				self.elatstow = 0;
				if (mm == 3):
					self.elcount = self.elcount + fcount;
				else:
					self.elcount = self.elcount - fcount;
		#condition for switching axis to be moved (from el to az or from az to el)
		self.axis = self.axis +1
		if (self.axis>1): 
			self.axis = 0
		return

	def stow_antenna(self):
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " Sending Antenna to Stow"
		self.tostow = 1
		self.azcount = 0
		self.elcount = 0
		fcount = 0	
		#Start stow on elevation
		self.axis = 1
		
		#Rise Elevation to avoid moving azimuth on low elevation
		mm = 3
		count = 50
		cmd = "  move "+str(mm)+" "+str(count)+"\n"
		self.send_command(cmd)
		cmd_r = self.get_serialAnswer()
		self.antenna_positionStatus(mm, cmd_r, fcount)
		
		#Azimuth to Stow

		mm = 0
		count = 5000
		cmd = "  move "+str(mm)+" "+str(count)+"\n"
		
		self.send_command(cmd)
		cmd_r = self.get_serialAnswer()
		#cmd_r = sim_serialAnswer('T', mm, count)
		self.antenna_positionStatus(mm, cmd_r, fcount)
	
		#Elevation to Stow
		mm = 2
		cmd = "  move "+str(mm)+" "+str(count)+"\n"
		
		self.send_command(cmd)
		cmd_r = self.get_serialAnswer()
		#cmd_r = sim_serialAnswer('T', mm, count)
		self.antenna_positionStatus(mm, cmd_r, fcount)
		
		self.az = 0.0
		self.el = 0.0
		self.slew = 0
		self.lastSRTCom = 'stow'
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" Antenna stowed, az: "+ str(self.aznow) +" el: "+str(self.elnow)+ " azcount: "+ str(self.azcount)+ " elcount: "+ str(self.elcount)
		return 

	def make_SRTCommand(self):
		if (self.axis == 0):
			if (self.azzcount > (self.azcount * 0.5 - 0.5)):
				mm = 1;
				count = int((self.azzcount - self.azcount*0.5 + 0.5));
			if (self.azzcount <= (self.azcount * 0.5 + 0.5)):
				mm = 0;
				count = int((self.azcount * 0.5 - self.azzcount + 0.5));
		else:
			if (self.ellcount > (self.elcount*0.5 - 0.5)):
				mm = 3;
				count = int(self.ellcount - self.elcount*0.5 + 0.5);
			if (self.ellcount <= (self.elcount*0.5 + 0.5)):
				mm = 2;
				count = int(self.elcount* 0.5 - self.ellcount + 0.5);
		ccount = count;
		if ((count > p.countperstep) and (ccount > p.countperstep)):
			count = p.countperstep;
		#builds movement command
		cmd = "  move " + str(mm) + " " + str(count) + "\n";
		self.lastSRTCom = [int(time.time()), cmd]
		return [cmd, mm, count]
		
	def normalize_az(self):
	# azimuth value scaling
	# Fold AZ into reasonable range 
		az = self.az % 360
	# put az in range 180 to 540 
		if p.south == 0:
			az = az + 360.0;   
			if az > 540.0:
				az -= 360.0
			if az < 180.0:
				az += 360.0;
			
			if az > p.azlim2:
				az -= 360.0
			
		self.az = az
		return

	def get_cmd_inLimits(self):
		# region is for find the relation between commanded position and antenna limits, if (az,el) don't fall in any region then command is out of limits
		region1 = 0
		region2 = 0
		region3 = 0;
		az = self.az
		el = self.el
		#verifies if movement command is in limits
		if ((az >= p.azlim1) & (az < p.azlim2) & (el >= p.ellim1) & (el <= p.ellim2)):
			region1 = 1;
		if ((az > (p.azlim1 + 180.0)) & (el > (180.0 - p.ellim2))):
			region2 = 1;
		if ((az < (p.azlim2 - 180.0)) & (el > (180.0 - p.ellim2))):
			region3 = 1;
		if ((region1 == 0) & (region2 == 0) & (region3 == 0)):
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name+" cmd out of limits"
			return 0
		#	if (fstatus == 1 && track != 0):
		#		o.stroutfile(g, "* ERROR cmd out of limits");
		#		track = 0
		print "region 123: "+str(region1) + str(region2) + str(region3)
		return 1
		
	def check_flip(self):
		#coordinates flip is applied for non cassi mounts
		flip = 0
		if ((self.az > p.azlim2) & (p.pushrod == 0)):
			self.az -= 180.0;
			self.el = 180.0 - self.el;
			flip = 1;
		if ((self.az < p.azlim1) & (p.pushrod == 0) & (flip == 0)):
			self.az += 180.0;
			self.el = 180.0 - self.el;
			flip = 1;
		#print normalized commanded (az,el)
		#print "az: " + str(az) + " el: " + str(el)
		
		#Uncomment only if sure you are using a non-cassi mount
		#self.az = az
		#self.el = el
		return flip
	
	def get_azzcount(self):
		#computes relative antenna movement starting from antenna limits (real movement amount)
		azz = self.az - p.azlim1 + self.azoff;
		#print "azz: " + str(azz) 
		azscale = p.azcounts_per_deg
		#computes target number of counts on azimuth for commanded movement
		azzcount = azz*azscale
		#print "azz count: "+ str(azzcount)
		self.azzcount = azzcount
		return
		
	def get_ellcount(self):
		ell = self.el - p.ellim1 + self.eloff;
		#print "ell: " + str(ell)
		elscale = p.elcounts_per_deg
		#computes target number of counts on elevation for commanded movement
		# elcount: number of accumulated counts on elevation 
		# ellcount: elevation counts target for commanded movement
		if p.pushrod == 0: #non cassi mount
			ellcount = ell * elscale
		else:
			ellcount = p.rod1**2 + p.rod2**2 - 2.0 * p.rod1 * p.rod2 * math.cos((p.rod4 - self.el) * math.pi / 180.0) - p.rod3**2;
			if (ellcount >= 0.0):
				ellcount = (-math.sqrt(ellcount) + p.lenzero) * p.rod5;
			else:
				ellcount = 0;
		# increase in length drives to horizon
		#print "ell count: " + str(ellcount)
		self.ellcount = ellcount
		return

	def get_first_axis(self):
		if (self.ellcount > self.elcount * 0.5):
			self.axis = 1;# move in elevation first
		else:
			self.axis = 0;# move azimuth
		return
		
	def check_count(self, rec_count, count):
		#read back count < commanded count only when antenna reaches to stow position in other case there is a lost count problem
		if ((rec_count < count) & ((int(self.axis) == 0 & int(self.az) != int(p.azlim1))|(int(self.axis) == 1 & int(self.el) != int(p.ellim1)))):
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" error, lost count, comandar a stow position"
			error = 1
			sys.exit()
		else:
			error = 0
		return error
		
	def get_current_azelPosition(self):
		#updates current azimuth position 
		azscale = p.azcounts_per_deg
		aznow = p.azlim1 - p.azcor + self.azcount*0.5/azscale;
		if (aznow > 360.0):
			aznow = aznow- 360.0;
	
		#updates elevation movement variation
		if (p.pushrod == 0):
			ellnow = self.elcount * 0.5 / p.elscale;
		else:
			#print elcount
			ellnow = -self.elcount * 0.5 /p.rod5 + p.lenzero;
			ellnow = p.rod1**2 + p.rod2**2 - p.rod3**2 - ellnow**2
			ellnow = ellnow / (2.0 * p.rod1 * p.rod2);
			ellnow = -math.acos(ellnow) * 180.0 / math.pi + p.rod4 - p.ellim1;
			#print ellnow
	
		#updates current elevation position
		elnow = p.ellim1 - p.elcor + ellnow;
	
		#rescales current elevation and azimuth position
		if (elnow > 90.0):
			if (aznow >= 180.0):
				aznow = aznow - 180.0;
			else:
				aznow = aznow + 180.0;
				elnow = 180.0 - elnow;
		#print "az: " + str(aznow)+ " el: "+ str(elnow)
		self.aznow = aznow
		self.elnow = elnow
		return
		
	def check_limit(self):
		#determines if antenna is actually in stow position
		if ((abs(self.aznow - p.azlim1) < 0.2)):
			self.azatstow = 1
		if ((abs(self.elnow - p.ellim1) < 0.2)):
			self.elatstow = 1
		if (self.elatstow and self.azatstow):
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " + self.name+ " antenna at stow";
			self.slew = 0
		return
		
	def check_end(self):
		#determines if antenna reached to commanded position
		if ((abs(self.aznow - self.az) <= 0.2) & (abs(self.elnow - self.el) <= 0.2)):
			self.slew = 0
			self.OnTarget = True
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" movimiento terminado"
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" azcount: "+str(self.azcount)+ " elcount: " + str(self.elcount)
			self.portInUse[0] = False
		if self.aznow < p.azlim1:
			self.aznow = p.azlim1
			self.azcount = 0.0
		if self.elnow < p.ellim1:
			self.elnow = p.ellim1
			self.elcount = 0.0
		return
		
	def cmd_azel(self, az, el):
		self.OnTarget = False
		self.az = az
		self.el = el
		self.normalize_az()
		flip = self.check_flip()
		inLimits = self.get_cmd_inLimits()
		self.get_azzcount()
		self.get_ellcount()
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " az: "+ str(self.az) + " azzcount: "+str(self.azzcount) + " el: "+ str(self.el)+" ellcount: "+ str(self.ellcount)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" current position: az: "+ str(self.aznow)+ " el: "+str(self.elnow) 
		self.get_first_axis()
		self.slew_antenna()
		time.sleep(0.5)
		return
	
	def slew_antenna(self):
		self.slew = 1;
		while(self.slew == 1):
			for ax in range(0,2):
				status = ''
				[cmd, mm, count] = self.make_SRTCommand()
				if(count != 0):
					self.send_command(cmd)
					status = status + 'sending: '+ cmd[:-1] +' '
					#cmd_r = sim_serialAnswer('M', mm, count)
					cmd_r = self.get_serialAnswer()
				else:
					status = status + 'sending: nothing '
					cmd_r =  ['M', '0', '0', 'none']
				#cmd_r = get_serialAnswer(port)
				status = status + 'received: '+ str(cmd_r) + ' '
				[rec_count, fcount] = self.parseAnswer(cmd_r, count)
				count_error = self.check_count(rec_count, count)
				self.antenna_positionStatus(mm, cmd_r, fcount)
				self.get_current_azelPosition()
				status = status + "az: " + str(self.aznow) + " el: "+ str(self.elnow)
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " "+status
				self.check_limit()
				self.check_end()
				time.sleep(0.1)
		return
		
	def stop_slew(self):
	    self.slew = 0;
	    self.portInUse[0] = False
	    print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " "+ "stopping slew (azel_thread)"

	def load_parameters(self, pfile):
		global p
		p = importlib.import_module(pfile)
		self.azoff = p.azoff
		self.eloff = p.eloff
		self.azlim1 = p.azlim1
		self.azlim2 = p.azlim2
		self.ellim1 = p.ellim1
		self.ellim2 = p.ellim2
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" loaded parameters file " + str(p)
		if p.digital:
			self.receiver_default = '1a'
			self.receiver = self.receiver_default
			self.nfreq = p.receivers[self.receiver]['nfreq']
			self.freqsep = p.receivers[self.receiver]['freqsep']
			self.intg = p.receivers[self.receiver]['intg']
		self.calcons = p.calcons
		return
	
	#####################Radiometer functions
	def set_freq(self, new_fcenter, new_receiver):
	# This function is temporarily limited to change fcenter and receiver/mode
	#
	#
	#def set_freq(self, new_fcenter, new_nfreq, new_freqsep, new_receiver):
	#Set central frequency and receiver parameters
	#set freq (fcenter, nfreq, freqsep, receiver)		
	#por comando se puede configurar el receiver
	#if receiver = 0|0a se puede configurar: fcenter, nfreq, freqsep
	#if receiver != 0|0a se puede configurar: fcenter, receiver
	#Si el receiver es digital:
	#if new receiver < 1 --> receiver = 1, 
	#if new receiver = 5 --> nfreq = 40, freqsep = 1.0, intg = 0.52488, luego 
	#	luego configura nfreq (nfreq_max = 500) y freqsep (freqsep_min = 1) si se ingresan
	#if new receiver < 5 se configura uno de los modos del 1a al 4 en receivers
		self.fcenter = new_fcenter
		#if (new_nfreq < 1):
		#	new_nfreq = 1
		#if (new_nfreq > 500):
		#	new_nfreq = 500
		if not(p.digital):
			self.nfreq = 40
			self.freqsep = 0.04
			#self.nfreq = new_nfreq
			#self.freqsep = new_freqsep
			self.receiver = '0a'
		else:
			if (int(new_receiver[0])<1):
				new_receiver = '1'
			self.receiver = str(new_receiver)
			self.nfreq = p.receivers[str(new_receiver)]['nfreq']
			self.freqsep = p.receivers[str(new_receiver)]['freqsep']
			self.intg = p.receivers[str(new_receiver)]['intg']
			#if (int(new_receiver)==5):
			#	self.nfreq = 40
			#	self.freqsep = 1.0
			#	self.intg = 0.52488
			#	try:
			#		self.nfreq = new_nfreq
			#		self.freqsep = new_freqsep
			#	except:
			#		pass	
			#else:
			#	self.nfreq = self.receivers[str(new_receiver)]['nfreq']
			#	self.freqsep = self.receivers[str(new_receiver)]['freqsep']
			#	self.intg = self.receivers[str(new_receiver)]['intg']
		return
	
	def vane_calibration(self):
		self.atten = 0 # attenuator to 0 (not used for digital = True)
		pwr0 = pwr1 = trecvr = 0
		if self.mancal == 0:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" moving load on feed"
			self.calibrator('in')
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" place load on feed"
			self.stopProc =1
			raw_input("press any key when done")
		self.stopProc = 0
		self.calon = 1
		self.fcenter
		self.spectra()
		self.fcenter
		istart = 0
		istop = self.nfreq
		if int(self.receiver[0]) > 0:
			istart = 10
			istop = self.nfreq -10
		for i in range(istart, istop):
			pwr1 += self.spec[i]
		pwr1 = float(pwr1)/(istop-istart)
		time.sleep(1)
		if self.mancal == 0:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" moving load out of feed"
			self.calibrator('out')
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " remove load"
			self.stopProc = 1
			raw_input("press any key when done")
		self.stopProc = 0
		self.calon = 0
		self.spectra()
		self.fcenter
		for i in range(istart, istop):
			pwr0 += self.spec[i]
		pwr0 = float(pwr0)/(istop-istart)
		
		if (pwr1 > pwr0 and pwr0 > 0.0):
			trecvr = (p.tload - (pwr1/pwr0)*p.tspill)/( (pwr1/pwr0) - 1.0)
			self.tsys = trecvr + p.tspill
			self.calcons = ((trecvr + p.tspill)*self.calcons/ pwr0)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" tsys: ", self.tsys, " K"
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" calcons", self.calcons
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" trec: :", trecvr, " K"
			self.docal = 0
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+"tsys: error"
		return

	def noise_calibration(self):
		self.atten = 0 # attenuator to 0 (not used for digital = True)
		pwr0 = pwr1 = trecvr = 0
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " turning on noise diode"
		self.calibrator('noise_on')
		self.calon = 2
		self.fcenter
		self.spectra()
		self.fcenter
		istart = 0
		istop = self.nfreq
		if int(self.receiver[0]) > 0:
			istart = 10
			istop = self.nfreq -10
		for i in range(istart, istop):
			pwr1 += self.spec[i]
		pwr1 = float(pwr1)/(istop-istart)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" turning off noise diode"
		self.calibrator('noise_off')
		self.calon = 0
		self.spectra()
		self.fcenter
		for i in range(istart, istop):
			pwr0 += self.spec[i]
		pwr0 = float(pwr0)/(istop-istart)
		
		if (pwr1 > pwr0 and pwr0 > 0.0 and p.noisecal > 0.0):
			trecvr = ( p.noisecal / (pwr1/pwr0 - 1)) - p.tspill
			self.tsys = trecvr + p.tspill
			self.calcons = ((trecvr + p.tspill)*self.calcons/ pwr0)
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" tsys: ", self.tsys, " K"
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" calcons", self.calcons
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" trec: :", trecvr, " K"
			self.docal = 0
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" tsys: error"
		return

	def calibrator(self, pos):
		if pos=='noise_on':
			mode = 7
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " waiting on noise on  "
		if pos=='noise_off':
			mode = 6
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" waiting on noise off  "
		if pos=='in':
			mode = 5
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" waiting on calin  "
		if pos=='out':
			mode = 4
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" waiting on calout"
		cmd = "  move " + str(mode) + " 0 \n"
		self.send_command(cmd)
		cmd_r = self.get_serialAnswer()
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " Done"
		return
	
	def radiodg(self, freq):
		#freq in MHz
		self.avpower = 0
		self.power = 0
		self.a =0
		self.sampleStamp = []
		j = int(freq*(1.0/0.04)+0.5)
		mode = int(self.receiver[0]) - 1
		if (mode < 0 or mode == 4 or mode == 5):
			mode = 0
		b8 = (mode)
		b9 = (j & 0x3f)
		b10= ((j >> 6) & 0xff)
		b11= ((j >> 14) & 0xff)
		try:
			msg = struct.pack('b4s4b', 0, 'freq', b11, b10, b9, b8)
		except:
			#in case of error in the freq value de 1420.4 equivalent is set
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " error in freq value, setting freq to 1420.4"
			msg = struct.pack('b4s4b', 0, 'freq', 2, 42, 54, 0)
		self.freqa = (((b11*256.0 + (b10 & 0xff))*64.0 + (b9 & 0xff))*0.04 - 0.8)
		#Enviar comando por puerto serial y esperar respuesta en variable recv
		#simulacion#
		self.send_command(msg)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " freq request enviado"
		self.receiving = True
		while self.receiving:
			if self.port.inWaiting() >= 128:
				self.receiving = False
			else:
				pass
		data = self.port.read(128)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" recibido"
		recv = struct.unpack('!64H', data)
		#####
		for i in range(64):
			if (i<=31):
				k = (i+32)
			else:
				k = (i-32)
			power = recv[k]
			if (int(self.receiver[0])<5):
				a = (i-32) * self.freqsep * 0.4
			else:
				a = 0
			if p.graycorr[i] > 0.8:
				power = power / (p.graycorr[i] * (1.0 + a * a * p.curvcorr))
			
			a = self.calcons * power
			if i>0:
				self.specd[64-i] = a
			else:
				self.specd[0] = a
			if (i>=10 and i<54):
				self.avpower += power
		
		self.avpower = self.avpower /44.0 
		self.a = self.calcons * self.avpower
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" "+str(self.avpower)+" "+str(self.a)
		self.sampleStamp = [self.name, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), self.aznow, self.elnow, self.a]
		return
		
	def spectra(self):
		self.waitingSp = True
		avp = 0.0
		if ( int(self.receiver[0]) == 0 or int(self.receiver[0]) == 5):
			for i in range(self.nfreq):
				freqf = self.fcenter + (i - float(self.nfreq)/2) * self.freqsep + 0.8;
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" scanning channel " + str(i)+ " at freq " + str(freqf) + "receiver in mode: " + str(self.receiver[0])
				self.radiodg(freqf)
				self.spec[i] = self.a
				if i == 0:
					self.freq0 = self.freqa
			
			#The next routine could be move for scan and BeamSW functions
			for i in range(self.nfreq):
				pwr = self.spec[i]
				if pwr>0.0:
					avp += pwr
				if self.sig:
					self.avspec[i] = pwr
				else:
					self.avspecc[i] = pwr
				
				#if self.scan != 0:
				#	self.pwr[scan-1] = self.pwr[scan-1] + pwr
		else:
			if int(self.receiver[0]) == 4:
				nk = 3
			else:
				nk = 1
			
			for k in range(nk):
				nk2 = nk/2
				freqf = self.fcenter + (k - nk2)*0.36 + 0.8
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" scanning band " + str(k)+ " at freq " + str(freqf) + "receiver in mode: " + str(self.receiver[0])
				self.radiodg(freqf)
				if(k == nk2):
					self.fcenter = self.freqa
				
				if(k == 0):
					if int(self.receiver[0]) <= 3:
						self.freq0 = self.fcenter - 32.0*self.freqsep
					else:
						self.freq0 = self.fcenter - 78.0*self.freqsep
				
				for i in range(64):
					pwr = self.specd[i]
					self.spec[i+k*64] = pwr
					
			if int(self.receiver[0]) == 4:
				pwr = 0.0
				for k in range(3):
					i = 54 + k
					j = 64 + 8 + k
					pwr += self.spec[i] - self.spec[j]
					i = 54 + 64 + k
					j = 128 + 8 + k
					pwr += self.spec[i] - self.spec[j]					
				slope = pwr / 276.0
				
				for k in range(3):
					for i in range(64):
						j = i + k*64
						pwr = self.spec[j] - (i - 32)*slope
						self.spec[j] = pwr
			
			for k in range(nk):
				for i in range(64):
					j = 1
					n = 46*j + i
					if k == 0:
						if i > 55:
							j = 0
					if k == 1:
						if (i < 10 or i > 55):
							j = 0
					if k == 2:
						if i < 10:
							j = 0
					if j == 1:
						pwr = self.spec[i + k*64]
						self.spec[n] = pwr
						if pwr > 0:
							if (n >=10 and n < self.nfreq - 10):
								avp += pwr
								#if self.scan != 0:
								#	self.pwr[scan-1] = self.pwr[scan-1] + pwr  
							if self.sig:
								self.avspec[n] = self.avspec[n] + pwr
							else:
								self.avspecc[n] =self.avspecc[n] + pwr
								
		
			if int(self.receiver[0]) >0:
				avp = float(avp) / (self.nfreq - 20)
			else:
				avp = avp / self.nfreq
			
			if self.bswlast > 0.0:
				if self.sig:
					pp = avp - self.bswlast
				else:
					pp = self.bswlast - avp
				self.bswav = self.bswav + pp
				self.bswsq = self.bswsq + pp**2
				self.bswcycles = self.bswcycles + 1
			
			self.bswlast = avp
			if self.sig:
				self.av = self.av + 1
			else:
				self.avc = self.avc + 1
		self.waitingSp = False
		self.sampleStamp.append(self.freq0)
		self.sampleStamp.append(self.av)
		self.sampleStamp.append(self.avc)
		self.sampleStamp.append(self.freqsep)
		self.sampleStamp.append(self.nfreq)
		self.avspecs = [x / (self.av+1e-6) for x in self.avspec]
		self.avspeccs = [x / (self.avc+1e-6) for x in self.avspecc]
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" av:", self.av, "avc:", self.avc
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" avspec", max(self.avspec), max(self.avspecs)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" avspecc", max(self.avspecc), max(self.avspeccs)
		self.portInUse[0] = False
		time.sleep(0.5) # wait before end the thread
		return self.spec, self.avspecs, self.avspeccs, self.specd
	
	def clear(self):
		#CLEAR SPECTRUM DATA
		self.spec = [0]*256
		self.avspec = [0]*256
		self.avspecc = [0]*256
		self.bswav = 0.0 
		self.bswsq = 0.0
		self.bswlast = 0.0
		self.bswcycles = 0.0
		self.av = 0.0
		self.avc = 0.0
		self.paver = 0.0
		self.prms =0.0
		self.pnum = 1e-6
		return
		
		####### Threads
	def azel_thread(self, az, el):
		#while(self.receiving):
		#	time.sleep(0.1)
		#if self.slew ==0: Modificado por mejora
		if not self.portInUse[0]: # Nueva linea
			self.portInUse = [True, 'AzEl']
			azel_thread = threading.Thread(target = self.cmd_azel, args=(az,el), name = 'AzEl')
			azel_thread.start()
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " SerialPort busy: " + str(self.portInUse)
			if self.portInUse[1]=='AzEl':
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" Wait antenna to reach commanded position"
			if self.portInUse[1]=='spectra':
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" wait until spectrum is received"
		return
		
	def status_thread(self, disp):
		status_thread = threading.Thread(target = self.status, args=(disp))
		status_thread.start()
		return
		
	def spectra_thread(self):
		if not self.portInUse[0]: # Nueva linea
			self.portInUse = [True, 'spectra']
			#self.waitingSp = True
			spectra_thread = threading.Thread(target = self.spectra, args=[], name = 'Spectra')
			spectra_thread.start()
		else:
			print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+ " SerialPort busy: " + str(self.portInUse)
			if self.portInUse[1]=='AzEl':
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" Wait antenna to reach commanded position"
			if self.portInUse[1]=='spectra':
				print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" wait until spectrum is received"
		return
		######### Single Dish / ARI_signalHound Switch
	def SD_ARI_Switch_init(self):
		self.SwitchPin = 25
		self.SwitchFeedbackPin = 23
		relay2 = 17
		relay2_read = 24
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.SwitchFeedbackPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
		#GPIO.setup(relay2_read, GPIO.IN, pull_up_down = GPIO.PUD_UP)
		GPIO.setup(self.SwitchPin, GPIO.OUT)
		#GPIO.setup(relay2, GPIO.OUT)
		GPIO.add_event_detect(self.SwitchFeedbackPin, GPIO.RISING, callback=self.printSwitch1, bouncetime=300)
		#GPIO.add_event_detect(relay2_read, GPIO.FALLING, callback=printRelay2, bouncetime=300)

	def printSwitch1(self,channel):
		print("Button 1 pressed!")

	#def printRelay2(channel):
	#   print("Button 2 pressed!")

	def end(self):
		GPIO.cleanup()
		GPIO.remove_event_detect(self.SwitchFeedbackPin)
		#GPIO.remove_event_detect(relay2_read)

	def on(self, pin):
		GPIO.output(pin, True)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" Switching receiver to ARI"

	def off(self, pin):
		GPIO.output(pin, False)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" Switching receiver to SD"

	def GPstatus(self):
		SD_ARI_Switch = GPIO.input(self.SwitchFeedbackPin)
		#relay2 = GPIO.input(relay2_read)
		print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+" " +self.name+" SD_ARI_Switch: " + str(relay1)
		#print "relay 2: " + str(relay2)

	def SD_ARI_Switch(self, mode):
		if (mode == 'ARI'):
			self.off(self.SwitchPin)
		if (mode == 'SD'):
			self.on(self.SwitchPin)

	#def R2(state):
	#    if state:
	#        on(relay2)
	#    else:
	#        off(relay2)


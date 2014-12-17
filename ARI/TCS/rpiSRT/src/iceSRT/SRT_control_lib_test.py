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

global port 
global p

print "importing SRT library"

class Antenna:
	def __init__(self):
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
		
	def status(self, disp):
		if(disp == True):
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
		return self.az, self.el, self.aznow, self.elnow, self.axis, self.tostow, self.elatstow, self.azatstow, self.slew, self.serialport, str(self.lastSRTCom), str(self.lastSerialMsg)
		
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
		while(finished == 0):
			cmd_r = cmd_r + self.port.read(self.port.inWaiting())
			if(cmd_r.find('\r') !=-1):
				finished = 1
			else:
				cmd_r = cmd_r +self.port.read(self.port.inWaiting())
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
			print "error, comandar a stow position"
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
			print "elevation at stow position"
			self.elatstow = 1;
			self.elcount = 0
			self.elnow = p.ellim1;
	
		#condition for entering azimuth stow position
		if ((mm == 0) & (cmd_r[0] == 'T') & (self.tostow == 1)):
			print "azimuth at stow position"
			self.azatstow = 1;
			self.azcount = 0;
			self.aznow= p.azlim1
	
		#Time out from antenna
		if ((cmd_r[0] == 'T') & (self.tostow == 0)):
			print "timeout from antenna, command to stow"
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
		print "Sending Antenna to Stow"
		self.tostow = 1
		self.azcount = 0
		self.elcount = 0
		#Start stow on elevation
		self.axis = 1
		
		fcount = 0	
		mm = 2
		count = 5000
		cmd = "  move "+str(mm)+" "+str(count)+"\n"
		
		self.send_command(cmd)
		cmd_r = self.get_serialAnswer()
		#cmd_r = sim_serialAnswer('T', mm, count)
		self.antenna_positionStatus(mm, cmd_r, fcount)
	
		mm = 0
		cmd = "  move "+str(mm)+" "+str(count)+"\n"
		
		self.send_command(cmd)
		cmd_r = self.get_serialAnswer()
		#cmd_r = sim_serialAnswer('T', mm, count)
		self.antenna_positionStatus(mm, cmd_r, fcount)
		
		self.az = 0.0
		self.el = 0.0
		self.lastSRTCom = 'stow'
		print "Antenna stowed, az: "+ str(self.aznow) +" el: "+str(self.elnow)+ " azcount: "+ str(self.azcount)+ " elcount: "+ str(self.elcount)
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
			print "cmd out of limits"
			sys.exit()
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
		azz = self.az - p.azlim1;
		#print "azz: " + str(azz) 
		azscale = p.azcounts_per_deg
		#computes target number of counts on azimuth for commanded movement
		azzcount = azz*azscale
		#print "azz count: "+ str(azzcount)
		self.azzcount = azzcount
		return
		
	def get_ellcount(self):
		ell = self.el - p.ellim1;
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
			print "error, lost count, comandar a stow position"
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
		if ((abs(self.aznow - p.azlim1) < 0.1) & (abs(self.elnow - p.ellim1) < 0.1)):
			print "antenna at stow";
			self.azatstow = 1
			self.elatstow = 1
			self.slew = 0
		return
		
	def check_end(self):
		#determines if antenna reached to commanded position
		if ((abs(self.aznow - self.az) <= 0.2) & (abs(self.elnow - self.el) <= 0.2)):
			self.slew = 0
			print "movimiento terminado"
			print "azcount: "+str(self.azcount)+ " elcount: " + str(self.elcount)
		return
		
	def cmd_azel(self, az, el):
		self.az = az
		self.el = el
		self.normalize_az()
		flip = self.check_flip()
		inLimits = self.get_cmd_inLimits()
		self.get_azzcount()
		self.get_ellcount()
		print "az: "+ str(self.az) + " azzcount: "+str(self.azzcount) + " el: "+ str(self.el)+" ellcount: "+ str(self.ellcount)
		print "current position: az: "+ str(self.aznow)+ " el: "+str(self.elnow) 
		self.get_first_axis()
		self.slew_antenna()
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
				print status
				self.check_limit()
				self.check_end()
				time.sleep(0.5)
		return

	def load_parameters(self, pfile):
		global p
		p = importlib.import_module(pfile)
		print "loaded parameters file " + str(p)
		return
	
	def azel_thread(self, az, el):
		azel_thread = threading.Thread(target = self.cmd_azel, args=(az,el), name = 'AzEl')
		azel_thread.start()
		return
		
	def status_thread(self, disp):
		status_thread = threading.Thread(target = self.status, args=(disp))
		status_thread.start()
		return
		
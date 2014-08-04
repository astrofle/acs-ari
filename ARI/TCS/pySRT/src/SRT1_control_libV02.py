#!/usr/bin/env python

import sys
import os
import math
import serial
import time
import parameters_srt1 as p
import ephem
import sources

def cmd_azel(az, el, azcount, elcount, aznow, elnow):
	az = normalize_az(az, p.south)
	inLimits = get_cmd_inLimits(az, el, p.azlim1, p.azlim2, p.ellim1, p.ellim2)
	#flip = check_flip(az,el, p.azlim1, p.azlim2, p.pushrod)
	azzcount = get_azzcount(az, p.azlim1, p.azcounts_per_deg)
	ellcount = get_ellcount(el, p.ellim1, p.lenzero, p.pushrod, p.elcounts_per_deg, p.rod1, p.rod2, p.rod3, p.rod4, p.rod5)
	print "az: "+ str(az) + " azzcount: "+str(azzcount) + " el: "+ str(el)+" ellcount: "+ str(ellcount)
	print "current position: az: "+ str(aznow)+ " el: "+str(elnow) 
	axis = get_first_axis(ellcount, elcount)
	[aznow, elnow, azcount, elcount, p.azatstow, p.elatstow] = slew_antenna(port, axis, az, el, azcount, elcount, azzcount, ellcount, p)
	return [aznow, elnow, azcount, elcount, p.azatstow, p.elatstow]

def slew_antenna(port, axis, az, el, azcount, elcount, azzcount, ellcount, p):
	slew = 1;
	while(slew == 1):
		status = ''
		for ax in range(0, 2):
			[cmd, mm, count] = make_SRTCommand(axis, azzcount, ellcount, azcount, elcount, p.countperstep)
			if(count != 0):
				send_command(port, cmd)
				status = status + 'sending: '+ cmd[:-1] +' '
				cmd_r = get_serialAnswer(port)
			else:
				status = status + 'sending: nothing '
				cmd_r =  ['M', '0', '0', 'none']
            
			status = status + 'received: '+ str(cmd_r) + ' '
			[rec_count, fcount] = parseAnswer(cmd_r, count)
			count_error = check_count(rec_count, count, axis, az, el, p.azlim1, p.ellim1)
			[p.azatstow, p.elatstow, azcount, elcount, axis] = antenna_positionStatus(mm, cmd_r, p.tostow, p.azatstow, p.elatstow, azcount, elcount, fcount, axis, p.azlim1, p.ellim1)
        
		[aznow, elnow] = get_current_azelPosition(azcount,  elcount, p)
		status = status + "az: " + str(aznow) + " el: "+ str(elnow)
		print status
		slew = check_limit(aznow, elnow, p, slew)
		slew = check_end(aznow, elnow, az, el, azcount, elcount, slew, azzcount, ellcount)
	return [aznow, elnow, azcount, elcount, p.azatstow, p.elatstow]

def stow_antenna(p):
    p.tostow = 1
    azcount = 0
    elcount = 0
    axis = 1
    fcount = 0
    count = 5000
    
    mm = 0
    cmd = "  move " + str(mm) + " " + str(count) + "\n"
    send_command(port, cmd)
    cmd_r = get_serialAnswer(port)
    
    [p.azatstow, p.elatstow, azcount, elcount, axis] = antenna_positionStatus(mm, cmd_r, p.tostow, p.azatstow, p.elatstow, azcount, elcount, fcount, axis, p.azlim1, p.ellim1)
    
    mm = 2
    cmd = "  move " + str(mm) + " " + str(count) + "\n"
    send_command(port, cmd)
    cmd_r = get_serialAnswer(port)
    
    [p.azatstow, p.elatstow, azcount, elcount, axis] = antenna_positionStatus(mm, cmd_r, p.tostow, p.azatstow, p.elatstow, azcount, elcount, fcount, axis, p.azlim1, p.ellim1)
    
    aznow = p.azlim1
    elnow = p.ellim1
    print "Antenna stowed, az: " + str(aznow) + " el: " + str(elnow) + " azcount: " + str(azcount) + " elcount: " + str(elcount)
    return [p.azatstow, p.elatstow, azcount, elcount, axis, aznow, elnow]

def init_com(p):
	port = '/dev/tty' + p.port
	ser = serial.Serial(port, baudrate = 2400, timeout = 10)
	return ser

def send_command(port, cmd):
	#print "sending :"+ cmd
	port.write(cmd)
	return

def get_serialAnswer(port):
	finished = 0;
	cmd_r = ''
	while(finished == 0):
		cmd_r = cmd_r + port.read(port.inWaiting())
		if(cmd_r.find('\r') != -1):
			finished = 1
		else:
			cmd_r = cmd_r + port.read(port.inWaiting())
		time.sleep(1)
	
	#parsed received answer
	cmd_r = cmd_r.split(' ')
	#print cmd_r
	return cmd_r

def normalize_az(az, south):
# azimuth value scaling
# Fold AZ into reasonable range 
	az = az % 360
# put az in range 180 to 540 
	if south == 0:
		az = az + 360.0;   
		if az > 540.0:
			az -= 360.0
		if az < 180.0:
			az += 360.0;
	return az

def get_cmd_inLimits(az, el, azlim1, azlim2, ellim1, ellim2):
	# region is for find the relation between commanded position and antenna limits, 
	#if (az,el) don't fall in any region then command is out of limits
	region1 = 0
	region2 = 0
	region3 = 0;
	#verifies if movement command is in limits
	if ((az >= azlim1) & (az < azlim2) & (el >= ellim1) & (el <= ellim2)):
		region1 = 1;
	if ((az > (azlim1 + 180.0)) & (el > (180.0 - ellim2))):
		region2 = 1;
	if ((az < (azlim2 - 180.0)) & (el > (180.0 - ellim2))):
		region3 = 1;
	if ((region1 == 0) & (region2 == 0) & (region3 == 0)):
		print "cmd out of limits"
		sys.exit()
	#	if (fstatus == 1 && track != 0):
	#		o.stroutfile(g, "* ERROR cmd out of limits");
	#		track = 0
	print "region 123: " + str(region1) + str(region2) + str(region3)
	return 1

def check_flip(az, el, azlim1, azlim2, pushrod):
	#coordinates flip is applied for non cassi mounts
	flip = 0
	if ((az > azlim2) & (pushrod == 0)):
		az -= 180.0;
		el = 180.0 - el;
		flip = 1;
	if ((az < azlim1) & (pushrod == 0) & (flip == 0)):
		az += 180.0;
		el = 180.0 - el;
		flip = 1;
	#print normalized commanded (az,el)
	#print "az: " + str(az) + " el: " + str(el)
	return flip

def get_azzcount(az, azlim1, azcounts_per_deg):
	#computes relative antenna movement starting from antenna limits (real movement amount)
	azz = az - azlim1;
	#print "azz: " + str(azz) 
	azscale = azcounts_per_deg
	#computes target number of counts on azimuth for commanded movement
	azzcount = azz*azscale
	#print "azz count: "+ str(azzcount)
	return azzcount

def get_ellcount(el, ellim1, lenzero, pushrod, elcounts_per_deg, rod1, rod2, rod3, rod4, rod5):
	ell = el - ellim1;
	#print "ell: " + str(ell)
	elscale = elcounts_per_deg
	#computes target number of counts on elevation for commanded movement
	# elcount: number of accumulated counts on elevation 
	# ellcount: elevation counts target for commanded movement
	if pushrod == 0: #non cassi mount
		ellcount = ell * elscale
	else:
		ellcount = rod1**2 + rod2**2 - 2.0 * rod1 * rod2 * math.cos((rod4 - el) * math.pi / 180.0) - rod3**2;
		if (ellcount >= 0.0):
			ellcount = (-math.sqrt(ellcount) + lenzero) * rod5;
		else:
			ellcount = 0;
	# increase in length drives to horizon
	#print "ell count: " + str(ellcount)
	return ellcount

def get_first_axis(ellcount, elcount):
	if (ellcount > elcount * 0.5):
		axis = 1;# move in elevation first
	else:
		axis = 0;# move azimuth
	return axis

def make_SRTCommand(axis, azzcount, ellcount, azcount, elcount, countperstep):
	if (axis == 0):
		if (azzcount > (azcount * 0.5 - 0.5)):
			mm = 1;
			count = int((azzcount - azcount*0.5 + 0.5));
		if (azzcount <= (azcount * 0.5 + 0.5)):
			mm = 0;
			count = int((azcount * 0.5 - azzcount + 0.5));
	else:
		if (ellcount > (elcount*0.5 - 0.5)):
			mm = 3;
			count = int(ellcount - elcount*0.5 + 0.5);
		if (ellcount <= (elcount*0.5 + 0.5)):
			mm = 2;
			count = int(elcount* 0.5 - ellcount + 0.5);
	ccount = count;
	if ((count > countperstep) and (ccount > countperstep)):
		count = countperstep;
	#builds movement command
	cmd = "  move " + str(mm) + " " + str(count) + "\n";
	return [cmd, mm, count]

def sim_serialAnswer(result, mm, count):
	cmd_r = result+" " + str(count) + " 0 " + str(mm) + "\r"
	cmd_r = cmd_r.split(' ')
	time.sleep(1)
	#print cmd_r
	return cmd_r

def parseAnswer(cmd_r, count):
	#Whenever answer first character is different from M or T then there is a communication failure
	if ((cmd_r[0] != "M") & (cmd_r[0] != "T")):
		print "error, comandar a stow position"
		sys.exit()
	else:
		#print "OK"
		rec_count = float(cmd_r[1]) #encoder count read back from antenna controller
		b2count = float(cmd_r[2]) #read back from antenna controller
	#count is >5000 for stow command, 
	#fcount = 2*rec_count = 2*count and updates the current axis count whit the encoder counts during last step
	if (count < 5000):
		fcount = count * 2 + b2count; # add extra 1/2 count from motor coast
	else:
		fcount = 0;
	return [rec_count, fcount]

def check_count(rec_count, count, axis, az, el, azlim1, ellim1):
	#read back count < commanded count only when antenna reaches to stow position in other case there is a lost count problem
	if ((rec_count < count) & ((int(axis) == 0 & int(az) != int(azlim1))|(int(axis) == 1 & int(el) != int(ellim1)))):
		print "error, lost count, comandar a stow position"
		error = 1
		sys.exit()
	else:
		error = 0
	return error

def antenna_positionStatus(mm, cmd_r, tostow, azatstow, elatstow, azcount, elcount, fcount, axis, azlim1, ellim1 ):
	#Stop position verification
	#condition for entering elevation stow position
	if ((mm == 2) & (cmd_r[0] == 'T') & (tostow == 1)):
		elatstow = 1;
		elcount = 0
		elnow = ellim1;
	
	#condition for entering azimuth stow position
	if ((mm == 0) & (cmd_r[0] == 'T') & (tostow == 1)):
		azatstow = 1;
		azcount = 0;
		aznow = azlim1
	
	#Time out from antenna
	if ((cmd_r[0] == 'T') & (tostow == 0)):
		print "timeout from antenna, command to stow"
		sys.exit()
	
	#axis current count azcount and elcount updated with count variation from last step fcount
	if (cmd_r[0] == 'M'):
		if (axis == 0):
			azatstow = 0;
			if (mm == 1):
				azcount = azcount + fcount;
			else:
				azcount = azcount - fcount;
		if (axis == 1):
			elatstow = 0;
			if (mm == 3):
				elcount = elcount + fcount;
			else:
				elcount = elcount - fcount;
	#condition for switching axis to be moved (from el to az or from az to el)
	axis = axis + 1
	if (axis > 1): 
		axis = 0
	return [azatstow, elatstow, azcount, elcount, axis]

def get_current_azelPosition(azcount, elcount, p):
	#updates current azimuth position 
	azscale = p.azcounts_per_deg
	aznow = p.azlim1 - p.azcor + azcount*0.5/azscale;
	if (aznow > 360.0):
		aznow = aznow- 360.0;
	
	#updates elevation movement variation
	if (p.pushrod == 0):
		ellnow = elcount * 0.5 / p.elscale;
	else:
		#print elcount
		ellnow = -elcount * 0.5 /p.rod5 + p.lenzero;
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
	return [aznow, elnow]

def check_limit(aznow, elnow, p, slew):
	#determines if antenna is actually in stow position
	if ((abs(aznow - p.azlim1) < 0.1) & (abs(elnow - p.ellim1) < 0.1)):
		print "antenna at stow";
		azatstow = 1
		elatstow = 1
		slew = 0
	return slew

def check_end(aznow, elnow, az, el, azcount, elcount, slew, azzcount, ellcount):
	#determines if antenna reached to commanded position
	if ((abs(aznow - az) <= 0.11) & (abs(elnow - el) <= 0.11)):
		slew = 0
		print "movimiento terminado"
		print "azcount: "+str(azcount)+ " elcount: " + str(elcount)
	return slew

def set_site(p):
	site = ephem.Observer()
	site.lon = p.lon
	site.lat = p.lat
	site.elevation = p.elevation
	return site

#def set_object(source):
	#if(source == 'Sun'):
		#object = ephem.Sun()
	#if(source == 'Mars'):
		#object = ephem.Mars()
	#if(source == 'Jupiter'):
		#object = ephem.Jupiter()
	#if (source == 'LMC'):
		#object = ephem.readdb("LMC,f|G,5:23:34,-69:45:24,0.9,2000,3.87e4|3.3e4")
	#if (source == '3C273'):
		#object = ephem.readdb("3C273,f|G,12:29:06.6997,+02:03:08.598,12.8,2000,34.02|25.17")
	#if (source == 'sgrA'):
		#object = ephem.readdb("sgrA,f|J,17:45:40.036,-29:00:28.17,0,2000")
	#if (source == 'G90'):
		#object = ephem.readdb("G90,f|J,21:13:44,48:12:27.17,0,2000")
	#if (source == 'G180'):
		#object = ephem.readdb("G180,f|J,05:43:11,29:1:20,0,2000")
	#if (source == 'Orion'):
		#object = ephem.readdb("Orion,f|J,05:35:17.3,-05:23:28,0,2000")
	#if (source == 'Rosett'):
		#object = ephem.readdb("Rosett,f|J,06:31:51,04:54:47,0,2000")
	#return object

def source_azel(object, site):
	site.date = ephem.now()
	object.compute(site)
	az = 180*object.az/math.pi
	el = 180*object.alt/math.pi
	return [az, el]

def track_source(source, site, p, aznow, elnow, azcount, elcount, tracktime=2/60.):
    site = set_site(p)
    object = sources.set_object(source)
    timeout = time.time() + 60*tracktime
    while(1):
        [az, el] = source_azel(object, site)
        [aznow, elnow, azcount, elcount, p.azatstow, p.elatstow] = cmd_azel(az, el, azcount, elcount, aznow, elnow)
        time.sleep(2)
        if (time.time() > timeout):
            break
    return [aznow, elnow, azcount, elcount, p.azatstow, p.elatstow]

def noise_on():
	cmd = " move 7 0\n"
	send_command(port, cmd)

def noise_off():
	cmd = " move 6 0\n"
	send_command(port, cmd)
       
port = init_com(p)
site = set_site(p)
print "sending antenna to stow now!!"
[p.azatstow, p.elatstow, azcount, elcount, axis, aznow, elnow] = stow_antenna(p)
print " "
print "To command the antenna use:"
print "[SRT.aznow, SRT.elnow, SRT.azcount, SRT.elcount, SRT.p.azatstow, SRT.p.elatstow] = SRT.cmd_azel(az, el, SRT.azcount, SRT.elcount, SRT.aznow, SRT.elnow) "
print "changing only az and el parameters for the desired az-el coordinate"
print ""
print "To track a source use"
print "[SRT.aznow, SRT.elnow, SRT.azcount, SRT.elcount, SRT.p.azatstow, SRT.p.elatstow] = SRT.track_source('source', 'site', SRT.p, SRT.aznow, SRT.elnow, SRT.azcount, SRT.elcount)"
print ""
print "To stow antenna use:"
print "[p.azatstow, p.elatstow, azcount, elcount, axis, aznow, elnow] = stow_antenna(p)"

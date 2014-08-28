#!/usr/bin/env python

import sys
import os
import math
import serial
import time
import ephem
import sources

class SimPort():
    
    def __init__(self):
        rcvd = '\r'
        sent = '\r'
        
    def sim_serialAnswer(result, mm, count):
        cmd_r = result+" " + str(count) + " 0 " + str(mm) + "\r"
        cmd_r = cmd_r.split(' ')
        time.sleep(1)
        
        return cmd_r
        

class SRT():
    
    def __init__(self, antenna, sim=False):
        
        # Load configuration file
        if antenna == '1':
            import parameters_srt1 as p
            self.p = p
        elif antenna == '2':
            import parameters_srt2 as p
            self.p = p
        else:
            print 'Specified antenna not in array. Exiting\n'
            sys.exit()
        
        # Assign a serial port
        if sim:
            self.port = SimPort()
        else:
            self.port = self.init_com()
        
        self.site = self.set_site()
        
        [p.azatstow, p.elatstow, self.azcount, self.elcount, self.axis, self.aznow, self.elnow] = self.stow_antenna()

    def cmd_azel(self, az, el):
        az = self.normalize_az(az, self.p.south)
        inLimits = self.get_cmd_inLimits(az, el, self.p.azlim1, self.p.azlim2, self.p.ellim1, self.p.ellim2)
        #flip = check_flip(az,el, p.azlim1, p.azlim2, p.pushrod)
        azzcount = self.get_azzcount(az, self.p.azlim1, self.p.azcounts_per_deg)
        ellcount = self.get_ellcount(el, self.p.ellim1, self.p.lenzero, self.p.pushrod, \
                                     self.p.elcounts_per_deg, self.p.rod1, self.p.rod2, \
                                     self.p.rod3, self.p.rod4, self.p.rod5)
        print "az: {0} azzcount: {1} el: {2} ellcount {3}".format(az, azzcount, el, ellcount)
        print "current position: az: {0} el: {1}".format(self.aznow, self.elnow) 
        self.axis = self.get_first_axis(ellcount, self.elcount)
        [self.aznow, self.elnow, self.azcount, self.elcount, self.p.azatstow, self.p.elatstow] = \
         self.slew_antenna(az, el, azzcount, ellcount)
        return [self.aznow, self.elnow, self.azcount, self.elcount, self.p.azatstow, self.p.elatstow]

    def slew_antenna(self, az, el, azzcount, ellcount):
        slew = 1;
        while(slew == 1):
            status = ''
            for ax in range(0, 2):
                [cmd, mm, count] = self.make_SRTCommand(self.axis, azzcount, ellcount, self.p.countperstep)
                if(count != 0):
                    self.send_command(cmd)
                    status = status + 'sending: '+ cmd[:-1] +' '
                    cmd_r = self.get_serialAnswer()
                else:
                    status = status + 'sending: nothing '
                    cmd_r =  ['M', '0', '0', 'none']
                
                status = status + 'received: '+ str(cmd_r) + ' '
                [rec_count, fcount] = self.parseAnswer(cmd_r, count)
                count_error = self.check_count(rec_count, count, self.axis, az, el, self.p.azlim1, self.p.ellim1)
                [self.p.azatstow, self.p.elatstow, self.azcount, self.elcount, self.axis] = \
                  self.antenna_positionStatus(mm, cmd_r, fcount)
            
            [self.aznow, self.elnow] = self.get_current_azelPosition(self.p)
            status = status + "az: " + str(self.aznow) + " el: "+ str(self.elnow)
            print status
            slew = self.check_limit(slew)
            slew = self.check_end(az, el, azzcount, ellcount, slew)
        return [self.aznow, self.elnow, self.azcount, self.elcount, self.p.azatstow, self.p.elatstow]

    def stow_antenna(self):
        
        print "sending antenna to stow now!!"
        
        self.p.tostow = 1
        self.azcount = 0
        self.elcount = 0
        self.axis = 1
        fcount = 0
        count = 5000
        
        mm = 0
        cmd = "  move " + str(mm) + " " + str(count) + "\n"
        self.send_command(cmd)
        cmd_r = self.get_serialAnswer()
        
        [self.p.azatstow, self.p.elatstow, self.azcount, self.elcount, self.axis] = \
          self.antenna_positionStatus(mm, cmd_r, fcount)
        
        mm = 2
        cmd = "  move " + str(mm) + " " + str(count) + "\n"
        self.send_command(cmd)
        cmd_r = self.get_serialAnswer()
        
        [self.p.azatstow, self.p.elatstow, self.azcount, self.elcount, self.axis] = \
          self.antenna_positionStatus(mm, cmd_r, fcount)
        
        self.aznow = self.p.azlim1
        self.elnow = self.p.ellim1
        print "Antenna stowed, az: {0} el: {1} azcount: {2} elcount: {3}".format(self.aznow, self.elnow, self.azcount, self.elcount)
        return [self.p.azatstow, self.p.elatstow, self.azcount, self.elcount, self.axis, self.aznow, self.elnow]

    def init_com(self):
        port = '/dev/tty' + self.p.port
        ser = serial.Serial(port, baudrate=2400, timeout=10)
        return ser

    def send_command(self, cmd):
        #print "sending :"+ cmd
        self.port.write(cmd)
        return

    def get_serialAnswer(self):
        finished = 0
        cmd_r = ''
        while(finished == 0):
            cmd_r = cmd_r + self.port.read(self.port.inWaiting())
            if(cmd_r.find('\r') != -1):
                finished = 1
            else:
                cmd_r = cmd_r + self.port.read(self.port.inWaiting())
            time.sleep(1)
        
        #parsed received answer
        cmd_r = cmd_r.split(' ')
        #print cmd_r
        return cmd_r

    def normalize_az(self, az, south):
    # azimuth value scaling
    # Fold AZ into reasonable range 
        az = az % 360
    # put az in range 180 to 540 
        if south == 0:
            az = az + 360.0
            if az > 540.0:
                az -= 360.0
            if az < 180.0:
                az += 360.0
        return az

    def get_cmd_inLimits(self, az, el, azlim1, azlim2, ellim1, ellim2):
        # region is for find the relation between commanded position and antenna limits, 
        # if (az,el) don't fall in any region then command is out of limits
        region1 = 0
        region2 = 0
        region3 = 0
        #verifies if movement command is in limits
        if ((az >= azlim1) & (az < azlim2) & (el >= ellim1) & (el <= ellim2)):
            region1 = 1
        if ((az > (azlim1 + 180.0)) & (el > (180.0 - ellim2))):
            region2 = 1
        if ((az < (azlim2 - 180.0)) & (el > (180.0 - ellim2))):
            region3 = 1
        if ((region1 == 0) & (region2 == 0) & (region3 == 0)):
            print "cmd out of limits"
            sys.exit()
        #   if (fstatus == 1 && track != 0):
        #       o.stroutfile(g, "* ERROR cmd out of limits");
        #       track = 0
        print "region 123: " + str(region1) + str(region2) + str(region3)
        return 1

    def check_flip(self, az, el, azlim1, azlim2, pushrod):
        #coordinates flip is applied for non cassi mounts
        flip = 0
        if ((az > azlim2) & (pushrod == 0)):
            az -= 180.0
            el = 180.0 - el
            flip = 1
        if ((az < azlim1) & (pushrod == 0) & (flip == 0)):
            az += 180.0
            el = 180.0 - el
            flip = 1
        #print normalized commanded (az,el)
        #print "az: " + str(az) + " el: " + str(el)
        return flip

    def get_azzcount(self, az, azlim1, azcounts_per_deg):
        #computes relative antenna movement starting from antenna limits (real movement amount)
        azz = az - azlim1;
        #print "azz: " + str(azz) 
        azscale = azcounts_per_deg
        #computes target number of counts on azimuth for commanded movement
        azzcount = azz*azscale
        #print "azz count: "+ str(azzcount)
        return azzcount

    def get_ellcount(self, el, ellim1, lenzero, pushrod, elcounts_per_deg, rod1, rod2, rod3, rod4, rod5):
        ell = el - ellim1
        #print "ell: " + str(ell)
        elscale = elcounts_per_deg
        #computes target number of counts on elevation for commanded movement
        # elcount: number of accumulated counts on elevation 
        # ellcount: elevation counts target for commanded movement
        if pushrod == 0: #non cassi mount
            ellcount = ell * elscale
        else:
            ellcount = rod1**2 + rod2**2 - 2.0 * rod1 * rod2 * math.cos((rod4 - el) * math.pi / 180.0) - rod3**2
            if (ellcount >= 0.0):
                ellcount = (-math.sqrt(ellcount) + lenzero) * rod5
            else:
                ellcount = 0
        # increase in length drives to horizon
        #print "ell count: " + str(ellcount)
        return ellcount

    def get_first_axis(self, ellcount, elcount):
        if (ellcount > elcount * 0.5):
            self.axis = 1 # move in elevation first
        else:
            self.axis = 0 # move azimuth
        return self.axis

    def make_SRTCommand(self, axis, azzcount, ellcount, countperstep):
        if (self.axis == 0):
            if (azzcount > (self.azcount * 0.5 - 0.5)):
                mm = 1
                count = int((azzcount - self.azcount*0.5 + 0.5))
            if (azzcount <= (self.azcount * 0.5 + 0.5)):
                mm = 0
                count = int((self.azcount * 0.5 - azzcount + 0.5))
        else:
            if (ellcount > (self.elcount*0.5 - 0.5)):
                mm = 3
                count = int(ellcount - self.elcount*0.5 + 0.5)
            if (ellcount <= (self.elcount*0.5 + 0.5)):
                mm = 2
                count = int(self.elcount* 0.5 - ellcount + 0.5)
        ccount = count
        if ((count > countperstep) and (ccount > countperstep)):
            count = countperstep
        #builds movement command
        cmd = "  move " + str(mm) + " " + str(count) + "\n"
        return [cmd, mm, count]

    def parseAnswer(self, cmd_r, count):
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
            fcount = count * 2 + b2count # add extra 1/2 count from motor coast
        else:
            fcount = 0;
        return [rec_count, fcount]

    def check_count(self, rec_count, count, axis, az, el, azlim1, ellim1):
        #read back count < commanded count only when antenna reaches to stow position in other case there is a lost count problem
        if ((rec_count < count) & ((int(axis) == 0 & int(az) != int(azlim1))|(int(axis) == 1 & int(el) != int(ellim1)))):
            print "error, lost count, comandar a stow position"
            error = 1
            sys.exit()
        else:
            error = 0
        return error

    def antenna_positionStatus(self, mm, cmd_r, fcount):
        #Stop position verification
        #condition for entering elevation stow position
        if ((mm == 2) & (cmd_r[0] == 'T') & (self.p.tostow == 1)):
            self.p.elatstow = 1
            self.elcount = 0
            self.elnow = self.p.ellim1
        
        #condition for entering azimuth stow position
        if ((mm == 0) & (cmd_r[0] == 'T') & (self.p.tostow == 1)):
            self.p.azatstow = 1
            self.azcount = 0
            self.aznow = self.p.azlim1
        
        #Time out from antenna
        if ((cmd_r[0] == 'T') & (self.p.tostow == 0)):
            print "timeout from antenna, command to stow"
            sys.exit()
        
        #axis current count azcount and elcount updated with count variation from last step fcount
        if (cmd_r[0] == 'M'):
            if (self.axis == 0):
                self.p.azatstow = 0
                if (mm == 1):
                    self.azcount = self.azcount + fcount
                else:
                    self.azcount = self.azcount - fcount
            if (self.axis == 1):
                self.p.elatstow = 0
                if (mm == 3):
                    self.elcount = self.elcount + fcount
                else:
                    self.elcount = self.elcount - fcount
        #condition for switching axis to be moved (from el to az or from az to el)
        self.axis = self.axis + 1
        if (self.axis > 1): 
            self.axis = 0
        return [self.p.azatstow, self.p.elatstow, self.azcount, self.elcount, self.axis]

    def get_current_azelPosition(self, p):
        #updates current azimuth position 
        azscale = self.p.azcounts_per_deg
        aznow = self.p.azlim1 - self.p.azcor + self.azcount*0.5/azscale
        if (aznow > 360.0):
            aznow = aznow - 360.0
        
        #updates elevation movement variation
        if (p.pushrod == 0):
            ellnow = self.elcount*0.5/self.p.elscale;
        else:
            #print elcount
            ellnow = -self.elcount*0.5/self.p.rod5 + self.p.lenzero
            ellnow = self.p.rod1**2 + self.p.rod2**2 - self.p.rod3**2 - ellnow**2
            ellnow = ellnow / (2.0*self.p.rod1*self.p.rod2)
            ellnow = -math.degrees(math.acos(ellnow)) + self.p.rod4 - self.p.ellim1
            #print ellnow
        
        #updates current elevation position
        elnow = self.p.ellim1 - self.p.elcor + ellnow;
        
        #rescales current elevation and azimuth position
        if (elnow > 90.0):
            if (aznow >= 180.0):
                aznow = aznow - 180.0
            else:
                aznow = aznow + 180.0
                elnow = 180.0 - elnow

        #updates antenna position
        self.aznow = aznow
        self.elnow = elnow
        
        #returns antenna position
        return [aznow, elnow]

    def check_limit(self, slew):
        #determines if antenna is actually in stow position
        if ((abs(self.aznow - self.p.azlim1) < 0.1) & (abs(self.elnow - self.p.ellim1) < 0.1)):
            print "antenna at stow"
            slew = 0
        return slew

    def check_end(self, az, el, azzcount, ellcount, slew):
        #determines if antenna reached to commanded position
        if ((abs(self.aznow - az) <= 0.11) & (abs(self.elnow - el) <= 0.11)):
            slew = 0
            print "movement ended"
            print "azcount: {0} elcount: {1}".format(self.azcount, self.elcount)
        return slew

    def set_site(self):
        site = ephem.Observer()
        site.lon = self.p.lon
        site.lat = self.p.lat
        site.elevation = self.p.elevation
        return site

    def source_azel(self, source, t=None):
        if not t:
            t = ephem.now()
        self.site.date = t
        source.compute(self.site)
        az = math.degrees(source.az)
        el = math.degrees(source.alt)
        return [az, el]

    def track_source(self, source, tracktime=2/60.):
        
        timeout = time.time() + 60*tracktime
        while(1):
            [az, el] = self.source_azel(source)
            [self.aznow, self.elnow, self.azcount, self.elcount, self.p.azatstow, self.p.elatstow] = \
                         self.cmd_azel(az, el, self.azcount, self.elcount, self.aznow, self.elnow)
            #time.sleep(2)
            if (time.time() > timeout):
                break
        return [self.aznow, self.elnow, self.azcount, self.elcount, self.p.azatstow, self.p.elatstow]

    def noise_on(self):
        cmd = "  move 7 0\n"
        self.send_command(cmd)

    def noise_off(self):
        cmd = "  move 6 0\n"
        self.send_command(cmd)
       
#port = init_com(p)
#site = set_site(p)
#
#[p.azatstow, p.elatstow, azcount, elcount, axis, aznow, elnow] = stow_antenna(p)
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

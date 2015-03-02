#!/usr/bin/env python

import sys
import os
import math
import serial
import time

"""
global variables (maybe parameters)
vsrt:  0 for single antenna, 2 for interferometer
azelsim: Mount simulation
comerr: number of communication errors
south: 0 antenna normally to north, 1 antenna normally to south
azlim1, azlim2, ellim1, ellim2: antenna movement limits
fstatus: ??
track: ??
pushrod: 1 for cassi mount, 0 for any other
azcountsperdeg, elcountsperdeg: number of encoder counter per degree in el and az
azcount, elcount: number of current encoder counts
"""



#global variables initialization
vsrt = 0.0
comerr = 0
azelsim = 0
south = 0
countperstep = 50
slew = 0 # 1 is for antenna moving until reaching commanded position

#Antenna limits
azlim1 = 0.0
azlim2 = 355.0

ellim1 = 8.0
ellim2 = 85.0



#Antenna Geometry - needed for elevation calculus
pushrod = 1 #cassi mount, 0 for other kind of mount
rod1 = 14.25;      # rigid arm length 
rod2 = 16.5;       # distance from pusrod upper joint to el axis 
rod3 = 2.0;        # pushrod collar offset 
rod4 =110.0;      # angle at horizon 
rod5 =30.0;

lenzero = rod1**2 + rod2**2 - 2.0 * rod1 * rod2 * math.cos((rod4 - ellim1) * math.pi / 180.0) - rod3**2;
if (lenzero >= 0.0):
	lenzero = math.sqrt(lenzero);
else:
	lenzero = 0;

# counts to degrees scale
azcounts_per_deg = 8.0 * 32.0 * 60.0 / (360.0 * 9.0); # default for CASSI 
elcounts_per_deg = 52.0 * 27.0 / 120.0;

#Encoder status initialization
#azcount = 0
#elcount = 0

azatstow = 0
elatstow = 0
tostow = 0


#valid starting from stow
#aznow = azlim1
#elnow = ellim1

## corrections due to azimuth and elevation axis tilt, tilt is zero by default in other case azcor and elcor are calculated by antiltaz and antilel function in geom library
## as no tilt is measured no tilt corrections are included
azcor = 0 
elcor = 0

#verifies azimuth limits and antenna orientation 
if ((azlim2 > azlim1) & (azlim2 < 360.0)):
	south = 1  # normally South 
else:
    south = 0 # North 
    if azlim2 < 360.0:
		azlim2 = azlim2 + 360.0

print "azlim1 = "+ str(azlim1) + " azlim2 = "+ str(azlim2)
print "ellim1 = "+ str(ellim1) + " ellim2 = "+ str(ellim2)

# Local coordinates (Calama)
place = 'calama'
lat = '-22.5'
lon = '-68.9'
elevation = 2277

#Radio parameters
curvcorr =0.0
calcons = 0.1 # gain correction constant to put power in units of K */
tload = 300.0
noisecal = 200.0
tspill = 20.0
beamw = 7.0
pscale = 400.0
digital = True
		#receiver configuration
receivers = {
		'0':{'nfreq':500, 'freqsep':0.04, 'intg':0.1},
		'0a':{'nfreq':40, 'freqsep':0.04, 'intg':0.1},
		'1':{'nfreq':64, 'freqsep':0.0078125, 'intg':0.1},
		'1a':{'nfreq':64, 'freqsep':0.0078125,'intg':0.52488},
		'2':{'nfreq':64, 'freqsep':0.00390625, 'intg':1.04976},
		'3':{'nfreq':64, 'freqsep':0.001953125, 'intg':2.09952},
		'4':{'nfreq':156,'freqsep':0.0078125, 'intg':0.52488},
		'5':{'nfreq':40,'freqsep':1.0, 'intg':0.52488}
}


graycorr = [0]*64
cf = [1.000000, 1.006274, 1.022177, 1.040125, 1.051102, 1.048860, 1.033074, 1.009606,
0.987706, 0.975767, 0.977749, 0.991560, 1.009823, 1.022974, 1.023796, 1.011319,
0.991736, 0.975578, 0.972605, 0.986673, 1.012158, 1.032996, 1.025913, 0.968784,
0.851774, 0.684969, 0.496453, 0.320612, 0.183547, 0.094424, 0.046729, 0.026470,
0.021300]
for i in range(0,33):
	if (i < 32):
		graycorr[ i + 32]= cf[i];
	if (i < 33):
		graycorr[32 - i] = cf[i];




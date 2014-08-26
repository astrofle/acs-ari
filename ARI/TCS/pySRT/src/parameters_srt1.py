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

port = 'USB0'

vsrt = 0.0
comerr = 0
azelsim = 0
south = 0
countperstep = 50
slew = 0 # 1 is for antenna moving until reaching commanded position

#Antenna limits
azlim1 = 1.64
azlim2 = 359.0

ellim1 = 0.1
ellim2 = 89.0

#Antenna Geometry - needed for elevation calculus
pushrod = 1       #cassi mount, 0 for other kind of mount
rod1 = 14.25      # rigid arm length 
rod2 = 16.5       # distance from pusrod upper joint to el axis 
rod3 = 2.0        # pushrod collar offset 
rod4 = 110.0      # angle at horizon 
rod5 = 30.0

lenzero = rod1**2 + rod2**2 - 2.0 * rod1 * rod2 * math.cos((rod4 - ellim1) * math.pi / 180.0) - rod3**2
if (lenzero >= 0.0):
    lenzero = math.sqrt(lenzero)
else:
    lenzero = 0

# counts to degrees scale
azcounts_per_deg = 8.0 * 32.0 * 60.0 / (360.0 * 9.0) # default for CASSI 
elcounts_per_deg = 52.0 * 27.0 / 120.0

#Encoder status initialization
#azcount = 0
#elcount = 0

azatstow = 0
elatstow = 0
tostow = 0

#valid starting from stow
#aznow = azlim1
#elnow = ellim1

# corrections due to azimuth and elevation axis tilt, tilt is zero by default in other case azcor and elcor are calculated by antiltaz and antilel function in geom library
# as no tilt is measured no tilt corrections are included
azcor = 0 
elcor = 0

#verifies azimuth limits and antenna orientation 
if ((azlim2 > azlim1) & (azlim2 < 360.0)):
    south = 1  # normally South 
else:
    south = 0 # North 
    if azlim2 < 360.0:
        azlim2 = azlim2 + 360.0

print "azlim1 = " + str(azlim1) + " azlim2 = " + str(azlim2)
print "ellim1 = " + str(ellim1) + " ellim2 = " + str(ellim2)

# Local coordinates (Calama)
#place = 'calama'
#lat = '-22.5'
#lon = '-68.9'
#elevation = 2277

# Local coordinates (talagante)
place = 'PUC'
lat = '-33.66'
lon = '-70.93'
elevation = 342

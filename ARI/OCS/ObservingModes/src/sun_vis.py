#!/usr/bin/env python

import SHManager
import os
import time
import sys

import SRT1_control_libV02 as srt1
import SRT2_control_libV02 as srt2
import pointing_scan as ps

from numpy import mean

if __name__ == '__main__':
    
    from optparse import OptionParser
    
    p = OptionParser()

    p.add_option('-s', '--source', dest='source', type='str', default='Sun',
        help='Source to use as pointing calibrator. Defaults to the Sun.')
    p.add_option('-b', '--band_width', dest='bw', type='float', default=1e6,
        help='Detector bandwidth in Hz. Defaults to 1 MHz.')
    #p.add_option('-i', '--int_time', dest='inttime', type='float', default=1,
        #help='Integration time at each position. Defaults to 1 s.')
    opts, args = p.parse_args(sys.argv[1:])

    if args == []:
        print 'Please specify a folder to store data.\n'
        print 'Run with the -h flag to see all options.\n'
        print 'Exiting.'
        exit()
    else:
        folder = args[0] 

    # Set source to observe
    source = srt1.sources.set_object(opts.source)
    #source2 = srt2.sources.set_object('Sun')
    
    # Initialize the Signal Hound
    sh = SHManager.SHManager()
    sh.set_bw(opts.bw)
    sh.filename = '{0}/scan.txt'.format(folder)

    # Check if specified folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    offsets = [0.1*i for i in range(-100, 101)]
    
    az1 =  srt1.source_azel(source, srt1.site)[0]
    az2 =  srt2.source_azel(source, srt2.site)[0]
    while (az1 > 0 - offsets[0]) and (az2 > 0 - offsets[0]):
        az1 =  srt1.source_azel(source, srt1.site)[0]
        az2 =  srt2.source_azel(source, srt2.site)[0]
        ps.az_scan_both(srt1, srt2, source, offsets, sh, folder)

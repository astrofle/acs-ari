#!/usr/bin/env python

import SHManager
import os
import time
import sys
import sources

import SRT_control_libV03 as srt

from sh_modes import source_scan

if __name__ == '__main__':
    
    from optparse import OptionParser
    
    p = OptionParser()

    p.add_option('-a', '--antenna', dest='ant', type='str', default='1',
        help='Antenna to use. Default 1.')
    p.add_option('-s', '--source', dest='source', type='str', default='Sun',
        help='Source to use as pointing calibrator. Defaults to the Sun.')
    p.add_option('-b', '--band_width', dest='bw', type='float', default=1e6,
        help='Detector bandwidth in Hz. Defaults to 1 MHz.')
    p.add_option('-i', '--int_time', dest='inttime', type='float', default=1,
        help='Integration time at each position. Defaults to 1 s.')
    opts, args = p.parse_args(sys.argv[1:])

    if args == []:
        print 'Please specify a folder to store data.\n'
        print 'Run with the -h flag to see all options.\n'
        print 'Exiting.'
        sys.exit()
    else:
        folder = args[0]
        
    # Check if specified folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    ant = srt.SRT(opts.ant)
        
    # Set source to observe
    #source = srt1.sources.set_object(opts.source)
    source = sources.set_object(opts.source)
    
    # Initialize the Signal Hound
    sh = SHManager.SHManager()
    sh.set_bw(opts.bw)
    
    # First scan in azimuth
    sh.set_file_name('{0}/sun_AZ.txt'.format(folder))
    offsets_l = [(i,0) for i in range(-12, -5)]
    offsets_c = [(0.2*i,0) for i in range(-50, 50)]
    offsets_r = [(i,0) for i in range(5, 12)]
    offsets = offsets_l + offsets_c + offsets_r
    source_scan(ant, source, offsets, det=sh, itime=opts.inttime)
    
    # Then scan in elevation
    sh.set_file_name('{0}/sun_EL.txt'.format(folder))
    offsets_l = [(0,j) for j in range(-12, -5)]
    offsets_c = [(0,0.2*j) for j in range(-50, 50)]
    offsets_r = [(0,j) for j in range(5, 12)]
    offsets = offsets_l + offsets_c + offsets_r
    source_scan(ant, source, offsets, det=sh, itime=opts.inttime)

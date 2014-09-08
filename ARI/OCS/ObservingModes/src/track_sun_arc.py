#!/usr/bin/env python

import os
import sys
import arcModes
import arcpy

import SRT_control_libV03 as srt

if __name__ == '__main__':
    
    from optparse import OptionParser
    
    p = OptionParser()

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
        exit()
    else:
        folder = args[0]
        
    # Load antennas
    srt1 = srt.SRT('1')
    srt2 = srt.SRT('2')

    # Set source to observe
    source = srt1.sources.set_source(opts.source)
    
    # Initialize ARC
    arc = arcpy.ARCManager(bw=400e6)
    #sh.set_bw(opts.bw)
    arc.set_file_name('{0}/sun_scan'.format(folder))

    # Check if specified folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    arcModes.track_source(srt1, srt2, source, arc, tracktime=60)
    
    

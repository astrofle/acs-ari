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

    srt2 = srt.SRT('2')
        
    # Set source to observe
    #source = srt1.sources.set_object(opts.source)
    source = sources.set_object(opts.source)
    
    # Initialize the Signal Hound
    sh = SHManager.SHManager()
    sh.set_bw(opts.bw)
    sh.set_file_name('{0}/scan.txt'.format(folder))

    offsets = [(i,j) for j in range(-12, 13) for i in range(-12, 13)]
    source_scan(srt2, source, offsets, det=sh, itime=opts.inttime)

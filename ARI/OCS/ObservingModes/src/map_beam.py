#!/usr/bin/env python

#import SHManager
import arcpy
import os
import time
import sys
import sources

import SRT_control_libV03 as srt

from obsmodes import source_scan

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
        
    # Set source to observe
    #source = srt1.sources.set_object(opts.source)
    source = srt.sources.set_source(opts.source)

    srt1 = srt.SRT('1')
    srt2 = srt.SRT('2')
    
    srt1.source_azel(source)
    # Initialize the detector
    #sh = SHManager.SHManager()
    #sh.set_bw(opts.bw)
    #sh.set_file_name('{0}/scan.txt'.format(folder))
    # Initialize ARC
    arc = arcpy.ARCManager(bw=100e6, ip='146.155.121.6', synth=True)
    arc.set_file_name('{0}/sun_beam_cal'.format(folder))
    
    # Calibrate
    [srt1.aznow, srt1.elnow, srt1.azcount, srt1.elcount, srt1.p.azatstow, srt1.p.elatstow] = \
             srt1.cmd_azel(10, 50)
    [srt2.aznow, srt2.elnow, srt2.azcount, srt2.elcount, srt2.p.azatstow, srt2.p.elatstow] = \
             srt2.cmd_azel(10, 50)
    srt1.noise_on()
    srt2.noise_on()
    srt1.source_azel(source) # required
    arc.make_head(ant1=srt1, ant2=srt2, source=source)
    for i in xrange(10):
        arc.get_spectrum()
        arc.write_spectrum()
        time.sleep(arc.get_tdump())
    srt1.noise_off()
    srt2.noise_off()
    srt1.source_azel(source)
    arc.make_head(ant1=srt1, ant2=srt2, source=source)
    for i in xrange(10):
        arc.get_spectrum()
        arc.write_spectrum()
        time.sleep(arc.get_tdump())
    
    arc.set_file_name('{0}/sun_beam'.format(folder))
    offsets = [(i,j) if i%2==0 else (i,-j) for i in range(-5, 5) for j in range(-5, 5)]
    source_scan(srt1, source, offsets, det=arc, ant2=srt2, itime=opts.inttime)

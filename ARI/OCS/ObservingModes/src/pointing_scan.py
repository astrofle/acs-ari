#import SHManager
import os
import time
import sys
from numpy import mean

def az_scan(antenna, source, offsets, detector, folder):
    """
    Performs a scan of source in the Azimut direction.
    It measures the power at the given offsets from the source.
    The telescope tracks the source as it moves.
    """

    print "Starting AZ scan of source %s." % source.name
    
    detector.set_file_name(folder + "/scan_az_%s.txt" % source.name)
    
    for i, o in enumerate(offsets):
        [az, el] = antenna.source_azel(source, antenna.site)
        [az, el] = [az + o, el + 0.0]
        [antenna.aznow, antenna.elnow, antenna.azcount, antenna.elcount, antenna.p.azatstow, antenna.p.elatstow] = \
             antenna.cmd_azel(az, el, antenna.azcount, antenna.elcount, antenna.aznow, antenna.elnow)
        #
        detector.get_spectrum()
        detector.write_spectrum(az, el)

    print "Done with AZ scan."

def az_scan_both(ant1, ant2, source, offsets, detector, folder, inttime=60):
    """
    Does an azimuth scan with both antennas.
    ----------------------------------------
    @param inttime: Integration time at each offset position
                    in seconds.
    """
    
    print "Starting AZ scan of source %s." % source.name

    oel = 0
    for i, oaz in enumerate(offsets):
        # Compute source position and apply azimut offset
        [az1, el1] = ant1.source_azel(source, ant1.site)
        [az2, el2] = ant2.source_azel(source, ant2.site)
        [offaz1, offel1] = [az1 + oaz, el1 + oel]
        [offaz2, offel2] = [az2 + oaz, el2 + oel]
        # Move antennas
        [ant1.aznow, ant1.elnow, ant1.azcount, ant1.elcount, ant1.p.azatstow, ant1.p.elatstow] = \
             ant1.cmd_azel(offaz1, offel1, ant1.azcount, ant1.elcount, ant1.aznow, ant1.elnow)
        [ant2.aznow, ant2.elnow, ant2.azcount, ant2.elcount, ant2.p.azatstow, ant2.p.elatstow] = \
             ant2.cmd_azel(offaz2, offel2, ant2.azcount, ant2.elcount, ant2.aznow, ant2.elnow)
        # Record
        timeout = time.time() + inttime
        while True:
            detector.get_spectrum()
            detector.write_spectrum(az1, el1, oaz, oel, az2, el2, oaz, oel)
            if time.time() > timeout:
                break

    print "Done with AZ scan."

def el_scan(antenna, source, offsets, detector):
    """
    Performs a scan of source in the Elevation direction.
    It measures the power at the given offsets from the source.
    The telescope tracks the source as it moves.
    """

    print "Starting EL scan of source %s." % source.name
    
    for i, o in enumerate(offsets):
        [az, el] = antenna.source_azel(source, antenna.site)
        [az, el] = [az + 0.0, el + o]
        [antenna.aznow, antenna.elnow, antenna.azcount, antenna.elcount, antenna.p.azatstow, antenna.p.elatstow] = \
             antenna.cmd_azel(az, el, antenna.azcount, antenna.elcount, antenna.aznow, antenna.elnow)
        detector.set_file_name(folder + "/scan_el_%i.txt" % i)
        detector.get_spectrum()
        detector.write_spectrum(az, el)

    print "Done with EL scan."
    
def source_scan(ant1, sou, off, ant2=None, det=None):
    """
    Scan the source with antenna at the given offsets.
    off must be a list of tuples containing the offsets in
    azimuth and elevation, e.g., off = [(1,0),(2,0),(3,0)],
    would scan the source at off sets (1,0), (2,0) and (3,0).
    """
    
    for x,y in off:
        [az1, el1] = ant1.source_azel(sou, ant1.site)
        [az1, el1] = [az1 + x, el1 + y]
        # Move antenna
        [ant1.aznow, ant1.elnow, ant1.azcount, ant1.elcount, ant1.p.azatstow, ant1.p.elatstow] = \
             ant1.cmd_azel(az1, el1, ant1.azcount, ant1.elcount, ant1.aznow, ant1.elnow)
        if ant2:
            [az2, el2] = ant2.source_azel(sou, ant2.site)
            [az2, el2] = [az2 + x, el2 + y]
            [ant2.aznow, ant2.elnow, ant2.azcount, ant2.elcount, ant2.p.azatstow, ant2.p.elatstow] = \
             ant2.cmd_azel(az2, el2, ant2.azcount, ant2.elcount, ant2.aznow, ant2.elnow)
        # Take data
        det.make_head(ant1=ant1, ant2=ant2, source=sou)
        det.get_spectrum()
        det.write_spectrum()
        
        
#START OF MAIN:
if __name__ == "__main__":
    from optparse import OptionParser

    p = OptionParser()

    p.add_option('-a', '--ant', dest='antenna', type='int', default=1,
        help='Which antenna to use, 1 or 2. Default is SRT1.')
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

    # Load the correct antenna control library
    if opts.antenna == 1:
        import SRT1_control_libV02 as SRT
    else:
        import SRT2_control_libV02 as SRT

    # Set source to observe
    source = SRT.set_object(opts.source)

    # Initialize the Signal Hound
    sh = SHManager.SHManager()
    sh.set_bw(opts.bw)

    # Check if specified folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    # EL scan
    el_offsets = range(-10, 11)
    el_scan(SRT, source, el_offsets, sh, folder)

    # AZ scan
    az_offsets = range(-10, 11)
    az_scan(SRT, source, az_offsets, sh, folder)

    print "Done with pointing scan."

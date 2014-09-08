#!/usr/bin/env python

import time

def hour_angle(site, source):
    """
    Computes the hour angle of a 
    source at a given site.
    """
    lst = site.sidereal_time()
    ha = lst - source.g_ra
    return ha

def track_source(ant1, ant2, source, detector, tracktime=60):
    """
    Performs a scan of source in the Azimut direction.
    It measures the power at the given offsets from the source.
    The telescope tracks the source as it moves.
    """

    print "Tracking source %s for tracktime %.2f minutes." % (source.name, tracktime)
    
    timeout = time.time() + 60*tracktime
    while time.time() < timeout:
        
        # Antenna movement
        [az1, el1] = ant1.source_azel(source, ant1.site)
        [az2, el2] = ant2.source_azel(source, ant2.site)
        [ant1.aznow, ant1.elnow, ant1.azcount, ant1.elcount, ant1.p.azatstow, ant1.p.elatstow] = \
             ant1.cmd_azel(az1, el1)
        [ant2.aznow, ant2.elnow, ant2.azcount, ant2.elcount, ant2.p.azatstow, ant2.p.elatstow] = \
             ant2.cmd_azel(az2, el2)
        
        # Phase correction
        ha = hour_angle(ant1.site, source)
        # the factor 0.21 converts to wavelengths 
        u,v,w = ant1.get_uvw(source.dec, ha)/0.21 
        # frequencies are in MHz
        tau_g = w / ((detector.fc + detector.lo_freq)*1e6) 
        delay_n = int(tau_g*detector.clck)
        print "Applying phase correction of {0} clock cycles".format(delay_n)
        if delay_n < 0:
            delay_n = -delay_n
            # 0 is the antenna input to ADC port I
            # Based on this, SRT1 should be connected to
            # the ADC input I
            detector.set_coarse_delay(1, delay_n) 
        else:
            detector.set_coarse_delay(0, delay_n)
        
        # Get spectrum
        detector.make_head(ant1=ant1, ant2=ant2, source=source)
        detector.get_spectrum()
        detector.write_spectrum()
        # Wait till next integration
        time.sleep(detector.get_tdump())

    print "Done with track."
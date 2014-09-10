#!/usr/bin/env python

import time
import ephem
    
def source_scan(ant1, sou, off, ant2=None, det=None, itime=1):
    """
    Scan the source with antenna at the given offsets.
    off must be a list of tuples containing the offsets in
    azimuth and elevation, e.g., off = [(1,0),(2,0),(3,0)],
    would scan the source at off sets (1,0), (2,0) and (3,0).
    """
    i = 0
    for x,y in off:
        [az1, el1] = ant1.source_azel(sou)
        [az1, el1] = [az1 + x, el1 + y]
        
        # Move antenna
        ant1.az_off = x
        ant1.el_off = y
        [ant1.aznow, ant1.elnow, ant1.azcount, ant1.elcount, ant1.p.azatstow, ant1.p.elatstow] = \
             ant1.cmd_azel(az1, el1)
        if ant2:
            ant2.az_off = x
            ant2.el_off = y
            [az2, el2] = ant2.source_azel(sou)
            [az2, el2] = [az2 + x, el2 + y]
            [ant2.aznow, ant2.elnow, ant2.azcount, ant2.elcount, ant2.p.azatstow, ant2.p.elatstow] = \
             ant2.cmd_azel(az2, el2)
        print "point {0}/{1}".format(i, len(off))
        # Take data
        if ant2:
            det.make_head(ant1=ant1, ant2=ant2, source=sou)
        else:
            det.make_head(ant1=ant1, source=sou)
        timeout = time.time() + itime
        while time.time() < timeout:
            det.get_spectrum()
            det.write_spectrum()
            try:
                time.sleep(det.get_tdump())
            except AttributeError:
                pass
        i += 1

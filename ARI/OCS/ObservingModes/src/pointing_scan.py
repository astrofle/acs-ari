import SRT1_control_libV02 as SRT1
import SRT2_control_libV02 as SRT2
import datetime as dt
import subprocess as sp

import time

sun = SRT1.set_object('Sun')

[az, el] = SRT1.source_azel(sun, SRT1.site)

azoff = 0
eloff = 0

# Initialize the signal hound and talk to it via a C++ script
sh = sp.Popen('./sh_loop', stdin = sp.PIPE)
sh.stdin.write('2\n')
sh.stdin.write('1e6\n')
sh.stdin.write('1\n')
sh.stdin.write('1 2\n')

for i in range(-5, 5):
    azoff = 0
    eloff = i*1
    [az, el] = SRT1.source_azel(sun, SRT1.site)
    [az, el] = [az + azoff, el + eloff]
    [SRT1.aznow, SRT1.elnow, SRT1.azcount, SRT1.elcount, SRT1.p.azatstow, SRT1.p.elatstow] = SRT1.cmd_azel(az, el, SRT1.azcount, SRT1.elcount, SRT1.aznow, SRT1.elnow)
    [SRT2.aznow, SRT2.elnow, SRT2.azcount, SRT2.elcount, SRT2.p.azatstow, SRT2.p.elatstow] = SRT2.cmd_azel(az, el, SRT2.azcount, SRT2.elcount, SRT2.aznow, SRT2.elnow)
    sh.stdin.write('4\n')
    sh.stdin.write('test_%i.txt\n' %i)
    sh.stdin.write('5\n')
    time.sleep(2)
    
sh.terminate()

#!usr/bin/env python

import CUSBSA
import sys
import ctypes
import time
import datetime

from math import log, ceil
    
def format_line(head, data, fmt=( '%Y-%m-%d-%H-%M-%S.%f {head} data: {data} \r\n' )):
   
    data_line = datetime.datetime.now().strftime(fmt).format(head=" ".join([str(h) for h in head]),
                                                             data=" ".join([str(x) for x in data]),)
    return data_line

class SHManager:
    def __init__(self, sim=False):
        self.sim = sim
        
        if self.sim:
            self.sh = None
        else:
            self.sh = CUSBSA.CUSBSA()
            
        self.MAXBW = 100e6
        self.MAXFREQ = 4.4e9
        
        self.bw = 40e6
        self.fc = 1420.4e6
        self.fi = 0.0;
        self.ff = 0.0;
        self.fft = 256
        self.rbw = 6400
        self.chw = 7500
        self.decimation = 1
        self.filename = "default.txt"
        self.acc_num = 0
        self.datafile = None
        self.ampl = []
        self.freq = []
        self.num_channel = 0
        self.update_freq()
        self.set_chw(self.chw)
        self.head = []
        self.power = 0.0

    def __del__(self):
        #clean up
        del(self.ampl)
        del(self.freq)

    def init_hound(self):
        print "Initializing the Signal Hound...",
        val = self.sh.Initialize()
        if val >= 100:
            print "Could not communicate with the SH Device, make sure it is connected and try again"
            sys.exit()
        print "Configuring SH...",
        self.sh.Configure(0.0, 1, 1, 1, 0, 0)
        print "done. Hound ready for hunting!"

    def update_freq(self):
        _fi = self.fc - self.bw/2.0
        _ff = self.fc + self.bw/2.0
        print "Update frequencies: existent fi %0.f will be updated to %0.f" % (self.fi, _fi)
        print "Update frequencies: existent ff %0.f will be updated to %0.f" % (self.ff, _ff)
        if _ff > self.MAXFREQ:
            print "new value of ff %0.f excceeds the maximum allowed value, %0.f will be used instead" % (_ff, self.MAXFREQ)
            _ff = self.MAXFREQ
        if _fi <= 0:
            print "new value of fi, %0.f, is a negative frequency. 1 Hz will be used instead" % _fi
            _fi = 1
        self.ff = _ff
        self.fi = _fi

    def set_bw(self, _bw):
        if (_bw > self.MAXBW):
            print "Requested bandwidth %0.f exceeds the maximum allowed value, %0.f will be used instead" % (_bw, self.MAXBW)
            _bw = self.MAXBW
        print "Set bandwidth: existent bw %0.f Hz will be updated to %0.f Hz" % (self.bw, _bw)
        self.bw = _bw 
        self.update_freq()

    def set_fc(self, _fc): 
        print "Set center frequency: existent fc %0.f Hz will be updated to %0.f Hz" % (self.fc, _fc)
        self.fc = _fc
        self.update_freq()

    def set_file_name(self, _filename):
        
        if self.datafile:
            self.datafile.close()
        
        print "Set file name: existent output file %s will be updated to %s" % (self.filename, _filename)
        
        self.filename = _filename
        self.datafile = open(self.filename, 'a')

    def set_fft(self, _fft):
        if not valid_fft_size(_fft):
            print "Invalid FFT size value of %0.f. It must be an integer power of 2." % _fft
            _fft = int(2**ceil(log(_fft, 2)))
            print "Will use %d instead." %_fft
        self.fft = _fft

    def get_spectrum(self): 
        print "Acquiring single spec ..."
        if self.fft <= 256:
            num_channel = self.sh.FastSweep(self.fi, self.ff, self.fft)
        else:
            num_channel = self.sh.SlowSweep(self.fi, self.ff, self.fft)
        print "num_channel %d " % num_channel

        # 64bit CUSBSA uses different variable names for trace amplitude and frequency
        pA = ctypes.cast( self.sh.dTraceAmpl.__long__(), ctypes.POINTER( ctypes.c_double ) )
        pF = ctypes.cast( self.sh.dTraceFreq.__long__(), ctypes.POINTER( ctypes.c_double ) )

        self.num_channel = num_channel
        self.ampl = []
        self.freq = []

        for i in range(0, num_channel):
            print "iteration %d" %i
            print pA[i]
            print pF[i]
            self.ampl.append(pA[i])
            self.freq.append(pF[i])
        self.acc_num += 1
        print "ready."

    def get_RBW(self):
        # This is not working with the 32bit SHLAPI
        #self.rbw = self.sh.m_dCalcRBW

        self.rbw = 1.6384e6/self.fft
        print "RBW: %2.2e" % self.rbw

    def chw_to_fftSize(self, _chw):
        """
        Converts a given channel width to a FFT size.
        """

        # If the channel width is larger than 5 kHz the SH should use FastSweep
        if _chw > 5e3:
            _fft = int(round(4.0e5/_chw))
        else:
            _fft = int(round(486111.111/_chw/self.decimation))
        
        return _fft

    def get_chw(self):
        """
        Gets the SH channel width.
        """
        if self.fft < 512:
            self.chw = int(round(4.0e5/self.fft))
        else:
            self.chw = int(round(486111.111/self.fft/self.decimation))

        print "Using channel width of %.0f" % self.chw

        return self.chw

    def set_chw(self, _chw):
        """
        Set the frequency separation of the output spectrum.
        This is not the same as the RBW.
        """
        _fft = self.chw_to_fftSize(_chw)
        self.set_fft(_fft)
        self.chw = self.get_chw()
   
    def write_spectrum(self):
        """
        Writes a line with a spectrum to the output file.
        """
        print "Writting data to %s ..." % self.filename
        if not self.datafile:
            self.datafile = open(self.filename, 'a')
        self.datafile.write(format_line(self.head, self.ampl))
        print "ready."
        
    def make_head(self, ant1=None, ant2=None, source=None):
        """
        Creates a list with observation data.
        The list is written at the beginning of
        each line in the output spectra.
        """
        
        minhead = ['fc', self.fc, 'bw', self.bw, 
                   'chw', self.chw, 'chnum', self.num_channel, 
                   'inum', self.acc_num]
    
        if source and ant1 and ant2:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow, 
                        'ant1_az', ant2.aznow, 'ant2_el', ant2.elnow,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num]
            except AttributeError:
                print "Header keyword not found, using minimum header."
                head = minhead

        elif source and ant1:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num]
            except AttributeError:
                print "Header keyword not found, using minimum header."
                head = minhead
                        
        elif ant1:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num]
            except AttributeError:
                print "Header keyword not found, using minimum header."
                head = minhead

        else:
            head = minhead

        self.head = head

        return head

    def spectral_power(self):
        self.power = 0.0
        for dbm in self.ampl:
            self.power += 10**(dbm/10)
        Pdbm = 10*math.log(power)
        print "spectral power is: " + str(Pdbm)
        return Pdbm

def valid_fft_size(fft):
    """
    Checks that the given FFT size is 
    a power of 2 different from 0.
    """
    num = int(fft)
    return num > 0 and (num & (num - 1)) == 0
    

       
if __name__ == "__main__":
    print "Starting SHManager"
    sh = SHManager()
    sh.init_hound()
    sh.set_bw(40e6)
    sh.set_fc(1421.0e6)
    sh.set_file_name("script_mode.txt")
    sh.get_spectrum()
    sh.make_head()
    sh.write_spectrum()


import CUSBSA
import sys
import ctypes
import time
import datetime
from numpy import mean

def time_stamp(msg='', fmt='Time: %Y-%m-%d-%H-%M-%S #{msg} \r\n'):
    return datetime.datetime.now().strftime(fmt).format(msg=msg)

class SHManager:
    def __init__(self):
        self.sh = CUSBSA.CUSBSA()
        self.MAXBW = 40e6
        self.MAXFREQ = 4.4e9
        self.bw = 40e6
        self.fc = 1420.4e6
        self.fi = 0.0;
        self.ff = 0.0;
        self.FFT = 256
        self.rbw = 6400
        self.decimation = 1
        self.filename = "default.txt"
        self.acc_n = 0
        self.amp = []
        self.freq = []
        self.num_channel = 0
        self.update_freq()

    def __del__(self):
        #clean up
        del(self.amp)
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
        print "Set file name: existent output file %s will be updated to %s" % (self.filename, _filename)
        self.filename = _filename

    def set_fft(self, _fft):
        if _fft % 2 != 0 or _fft == 0:
            print "Invalid FFT size value of %0.f. It must be an integer power of 2." % _fft
            _fft = 16
            print "Will use %d instead." %_fft
        self.FFT = _fft

    def get_spectrum(self): 
        print "Acquiring single spec ..."
        if self.FFT <= 256:
            num_channel = self.sh.FastSweep(self.fi, self.ff, self.FFT)
        else:
            num_channel = self.sh.SlowSweep(self.fi, self.ff, self.FFT)
        print "num_channel %d " %(num_channel)

        pA = ctypes.cast( self.sh.dTraceAmpl.__long__(), ctypes.POINTER( ctypes.c_double ) )
        pF = ctypes.cast( self.sh.dTraceFreq.__long__(), ctypes.POINTER( ctypes.c_double ) )

        self.num_channel = num_channel
        self.amp = []
        self.freq = []

        for i in range(0, num_channel):
            print "iteration %d" %i
            print pA[i]
            self.amp.append(pA[i])
            print pF[i]
            self.freq.append(pF[i])
        self.acc_n += 1
        print "ready."

    def get_RBW(self):
        # This is not working with the 32bit SHLAPI
        #self.rbw = self.sh.m_dCalcRBW

        self.rbw = 1.6384e6/self.FFT
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

    def set_chw(self, _chw):
        """
        Set the frequency separation of the output spectrum.
        This is not the same as the RBW.
        """
        _fft = self.chw_to_fftSize(_chw)
        self.set_fft(_fft)
   
    def write_spectrum(self):
        print "Writting data to %s ..." % self.filename
        f = open(self.filename, 'w')
        f.write( time_stamp() )
        for i in range(0, self.num_channel):
            f.write( "%0.10f    %0.10f \r\n" % (self.freq[i], self.amp[i]) )
        f.close()
        print "ready."

def valid_fft_size(_fft):
    """
    Checks that the given FFT size is 
    a power of 2 different from 0.
    """
    num = int(_fft)
    return num > 0 and (num & (num - 1)) == 0
       
if __name__ == "__main__":
    print "Starting SHManager"
    sh = SHManager()
    sh.init_hound()
    sh.set_bw(40e6)
    sh.set_fc(1421.0e6)
    sh.set_file_name("script_mode.txt")
    sh.get_spectrum()
    sh.write_spectrum()

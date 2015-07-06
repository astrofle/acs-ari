import sys, traceback, Ice
from time import sleep
import SHControl
import SHManager as SH
import threading
import os

import CUSBSA
import sys
import ctypes
import time
import datetime


class SHControlI(SHControl.SignalHound, SH.SHManager):
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
        
        self.name = 'SH'
        self.SH_initialized = False
        self.SH_freqUpdated = False
        self.SH_bwUpdated = False
        self.SH_fcUpdated = False
        self.SH_filenameUpdated = False
        self.SH_fftUpdated = False
        self.SH_spectrumUpdated = False
        self.SH_RBWUpdated = False
        self.SH_chwToFFTSizeUpdated = False
        self.SH_chwUpdated = False
        self.SH_writeUpdated = False
        self.SH_fileHeadUpdated = False
        self.SH_FFTSizeCheck = False
        self.SH_powerUpdated = False
        self.sampleStamp = SHControl.SHstamp()
        self.SH_Spectrum = SHControl.SHspectrum()

    def message(self, s, current = None):
        print s
        return s
    
    def SHinitHound(self, current = None):
        if (not self.SH_initialized):
            self.SH_initialized = False
            print "Initialising Signal Hound"
            self.init_hound()
            self.SH_initialized = True
        else:
            print "Signal Hound already initialized, skipping"
        return "Signal Hound initialized"

    def SHupdateFreq(self, current = None):
        self.SH_freqUpdated = False
        print "Updating Signal Hound frequency range"
        self.update_freq()
        self.SH_freqUpdated = True
        return "Signal Hound frequency range updated"

    def SHsetBW(self, bw, current = None):
        self.SH_bwUpdated = False
        print "Updating Signal Hound span"
        self.set_bw(bw)
        self.SH_bwUpdated = True
        return "Signal Hound span updated"
        
    def SHsetFc(self, fc, current = None):
        self.SH_fcUpdated = False
        print "Updating Signal Hound center frequency"
        self.set_fc(fc)
        self.SH_fcUpdated = True
        return "Signal Hound center frequency updated"

    def SHsetFileName(self, fn, current = None):
        self.SH_filenameUpdated = False
        print "Updating file name"
        self.set_file_name(fn)
        self.SH_filenameUpdate = True
        return "Signal Hound measurments file name updated"
    
    def SHsetFFT(self, fft, current = None):
        self.SH_fftUpdated = False
        print "Updating Signal Hound FFT size"
        self.set_fft(fft)
        self.SH_fftUpdated = True
        return "Signal Hound FFT size updated"
        
    def SHgetSpectrum(self, current = None):
        self.SH_spectrumUpdated = False
        print "Getting Signal Hound spectrum"
        self.get_spectrum()
        self.SH_spectrumUpdated = True
        _stamp = SHControl.SHstamp(self.sampleStamp[0], self.sampleStamp[1], self.sampleStamp[2], self.sampleStamp[3], self.sampleStamp[4], self.sampleStamp[5], self.sampleStamp[6], self.sampleStamp[7])
        _ampl = self.ampl
        SHsp = SHControl.SHspectrum(_stamp, _ampl)
        return SHsp

    def SHgetRBW(self, current = None):
        self.SH_RBWUpdated = False
        print "Updating Signal Hound RBW"
        self.get_RBW()
        self.SH_RBWUpdated = True
        return "Signal Hound RBW updated"

    def SHchwToFFTSize(self, chw, current = None):
        self.SH_chwToFFTSizeUpdated = False
        print "Calculating the FFT size for the channel width"
        FFT = self.chw_to_fftsice(chw)
        print "Done"
        self.SH_chwToFFTSizeUpdated = True
        return  "The FFT size is " + str(FFT)

    def SHgetCHW(self, current = None):
        self.get_chw()
        return "chw calculated"

    def SHsetCHW(self, chw, current = None):
        self.SH_chwUpdated = False
        print "Calculating the channel width"
        self.set_chw(chw)
        self.SH_chwUpdated = True
        return "The channel width is " + str(self.chw)

    def SHwriteSpectrum(self, current = None):
        self.SH_writeUpdated = False
        print "writing spectrum to file " + self.filename
        self.write_spectrum()
        self.SH_writeUpdated = True
        return "Signal hound spectrum written to file "+ self.filename

    def SHmakeHead(self, ant1, ant2, source, current = None):
        self.SH_fileHeadUpdated = False
        print "creating file head for spectrum data"
        self.make_head(ant1, ant2, source)
        self.SH_fileHeadUpdated = True
        return "file head for spectrum data created"
    
    def SHgetSpectralPower(self, current = None):
        self.SH_powerUpdated = False
        print "Obtaining Singal Hound spectral power"
        Pdbm = self.get_spectral_power()
        self.SH_powerUpdated = True
        print "spectral power is " + str(Pdbm[0])
        print "central frequenct power is " + str(Pdbm[1])
        return Pdbm 

    def SHvalidFFFSize(self, fft, current = None):
        self.SH_FFTSizeCheck = False
        print "Checking FFT size"
        check = self.valid_fft_size(fft)
        self.SH_FFTSizeCheck = True
        print "Done"
        return str(check)

    def SHStatus(self, current = None):
        _st = SHControl.state(self.name, self.SH_initialized, self.bw, self.fc, self.fi, self.ff,\
        self.fft, self.rbw, self.chw, self.decimation, self.acc_num, self.num_channel)
        return _st

try:
	if len(sys.argv)<2:
		print "use SRTcontrolServer.py  -h 192.168.0.6 -p 10000"
		sys.exit()
	IP =  ' '.join(sys.argv[1:])
	IP = "default -h " + IP
except:
	print "use SRTcontrolServer.py default -h 192.168.0.6 -p 10000 or 10001"
		
		
status = 0
ic = None
try:
	#ic = Ice.initialize(sys.argv)
	ic = Ice.initialize([''])
	#adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.6 -p 10000")
	print IP
	adapter = ic.createObjectAdapterWithEndpoints("SHController", IP)
	object = SHControlI()
	adapter.add(object, ic.stringToIdentity("SHController"))
	adapter.activate()
	print " SignalHound Server up and running!"
	ic.waitForShutdown()
except:
	traceback.print_exc()
	status = 1

if ic:
	#clean up
	try:
		ic.destroy()
	except:
		traceback.print_exc()
		status = 1

sys.exit(status)

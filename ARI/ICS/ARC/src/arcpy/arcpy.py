#!/usr/bin/env python
'''
This module provides functions to program and interact with a pocket correlator on a ROACH board.
It uses the Python KATCP library along with the katcp_wrapper distributed in the corr package. 
This is based on the script created by Jason Manley for the CASPER workshop.
Author: Pedro Salas, July 2014.
Modified:
'''

from __future__ import division

import corr,time,numpy,struct,sys,logging
import valon_synth as vs
import time
import datetime

katcp_port = 7147
roach_ip = '146.155.121.6'
synth_port = '/dev/valonsynth'
# Those that have been successful tested on the AIUC ROACH board
allowed_config = {100e6:[97656.25, 48828.125, 24414.0625],
                  400e6:[390625.0]}

def exit_fail(log_handler=None):
    if log_handler:
        print 'FAILURE DETECTED. Log entries:\n', log_handler.printMessages()
    else:
        print 'FAILURE DETECTED.\n'
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()
    
def arc_head(data, az1, el1, oaz1, oel1, az2, el2, oaz2, oel2, freq0, chw, nchan, accn, 
             fmt=( '%Y-%m-%d-%H-%M-%S.%f {az1} {el1} {oaz1} {oel1} {az2} {el2} {oaz2} '
                   '{oel2} {f0} {chw} {nchan} {accn} {data} \r\n' ), tdata='r'):
   
    #if tdata == 'c':
       #data_line = datetime.datetime.now().strftime(fmt).format(data=" ".join(["{c.real:.5f}+{c.imag:.5f}j".format(c=x) for x in data]),
                                                                #az1=az1, el1=el1, oaz1=oaz1, oel1=oel1,
                                                                #az2=az2, el2=el2, oaz2=oaz2, oel2=oel2,
                                                                #f0=freq0, chw=chw, nchan=nchan, accn=accn)
    #else:
    data_line = datetime.datetime.now().strftime(fmt).format(data=" ".join([str(x) for x in data]),
                                                                 az1=az1, el1=el1, oaz1=oaz1, oel1=oel1,
                                                                 az2=az2, el2=el2, oaz2=oaz2, oel2=oel2,
                                                                 f0=freq0, chw=chw, nchan=nchan, accn=accn)
    return data_line



class ARCManager():
    
    def __init__(self, bw=100e6, chw=97656.25, fft=1024, gain=1000, acc_len=2**28/1024, log_handler=None, ip='146.155.121.6', synth=None):

        # Opens the Valoon 5007 dual synth
        # SYNTH_B is the ADC clock, SYNTH_A the LO
        self.synth = synth
        if synth:
            self.synth = vs.Synthesizer(synth_port)
        
        # Sets general detector parameters
        # Separate real from imag output
        self.filename_abr = 'default_abr'
        self.filename_bar = 'default_bar'
        self.filename_abi = 'default_abi'
        self.filename_bai = 'default_bai'
        self.filename_aa = 'default_aa'
        self.filename_bb = 'default_bb'
        self.datafile_abr = None
        self.datafile_abi = None
        self.datafile_bar = None
        self.datafile_bai = None
        self.datafile_aa = None
        self.datafile_bb = None
        self.freq = []
        self.amp_a = []
        self.amp_b = []
        self.amp_ab = []
        self.amp_ba = []
    
        # Sets configuration parameters while checking some
        self.ip = ip
        self.bw = bw
        self.set_bw(bw)
        self.fft = fft
        self.chw = chw
        self.set_chw(chw)
        self.gain = gain
        self.acc_len = acc_len
        self.acc_num = 0
        
        # Writes firmware configuration to ROACH board
        self.log_handler = self._init_log(self.ip)
        self.fpga = self._connect_roach(katcp_port)
        self.boffile = self._config_to_boffile()
        self._set_bof_file()
        self.reset_firmware()
        self._set_fft_shift()
        self._set_acc_len(self.acc_len)
        self.set_gain()
        self.write = True
        
    def _config_to_boffile(self):
        """
        Outputs the .bof filename for a given bw and fft.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        """
        
        # Bandwidth is given in MHz in the .bof file names
        return 'arc_%d_%d.bof' % (self.bw/1e6, self.fft)
    
    def set_LO(self, lofreq):
        """
        Specifies LO frequency.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : LO frequency
            Frequency in MHz.
        """
        if not self.synth:
            print "No synthesizer on ROACH"
        else:
            self.synth.set_frequency(vs.SYNTH_A, lofreq)
        
    def set_write(self, write):
        """
        Configures the FPGA to output data or not.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : bool
            Write or not.
        """
        
        self.write = write
    
    def set_bw(self, bw):
        """
        Sets the FPGA band width.
        This will update the channel width to the
        closest one allowed for this bandwidth.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : float
            Band width. 100 MHz<BW<400 MHz.
        """
        
        if bw not in allowed_config.keys():
            bw = 100e6
            print 'Bandwidth not yet implemented. Using default of %0.f MHz.' % bw
        if not self.synth:
            print "No synthesizer on ROACH"
        else:
            self.synth.set_frequency(vs.SYNTH_B, 2*self.bw/1e6)
        self.bw = bw
        #self._update_boffile()
        
    def set_chw(self, chw):
        """
        Sets the FPGA channel width.
        The channel width will change
        with each band width change.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : float
            Channel width. Must be an allowed value.
        """
        
        fft = int(self.bw/self.chw)
        if chw not in allowed_config[self.bw]:
            fft = 1024
            chw = allowed_config[self.bw][0]
            print 'Channel width not implemented. Using default of %0.f kHz' % chw
        self.chw = chw
        self.fft = int(fft)
        #self._update_boffile()
    
    def _update_boffile(self):
        """
        Sets the FPGA bof file based on the current ARC configuration.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        """
        
        self.boffile = self._config_to_boffile()
        print 'Changing current .bof file to %s...' % self.boffile,
        self._set_bof_file(self.boffile)
        print '... done.'

    def get_chw(self):
        """
        Returns the current channel width.
        """
        
        print 'Using a channel width of %.0f' % self.chw
        return self.chw
    
    def get_bw(self):
        """
        Returns the current band width.
        """
        
        print 'Using a band width of %.0f' % self.bw
        return self.bw
        
    def _connect_roach(self, katcp_port=7147):
        """
        Connects to a ROACH board through katcp_port using the corr
        module.
        """
        
        print 'Connecting to server %s on port %i... ' % (self.ip, katcp_port),
        fpga = corr.katcp_wrapper.FpgaClient(self.ip, katcp_port, timeout=10, logger=self.log_handler)
        time.sleep(1)
        
        if fpga.is_connected():
            print 'ok\n'
        else:
            print 'ERROR connecting to server %s on port %i.\n' % (roach_ip, katcp_port)
            exit_fail(self.log_handler)
        
        return fpga
        
    def _init_log(self, ip):
        """
        Initializes the event log.
        """
        
        lh = corr.log_handlers.DebugLogHandler()
        logger = logging.getLogger(ip)
        logger.addHandler(lh)
        logger.setLevel(10)
        
        return logger
        
    def reset_firmware(self):
        """
        Resets the correlator firmware counters and triggers.
        """
        
        print 'Resetting board, software triggering and resetting error counters...',
        self.fpga.write_int('ctrl', 0) 
        self.fpga.write_int('ctrl', 1<<17) #arm
        self.fpga.write_int('ctrl', 0) 
        self.fpga.write_int('ctrl', 1<<18) #software trigger
        self.fpga.write_int('ctrl', 0) 
        self.fpga.write_int('ctrl', 1<<18) #issue a second trigger
        print 'done'
    
    def _set_bof_file(self):
        """
        Loads a .bof file into the FPGA.
        """
        
        print 'Programming FPGA with %s...' % self.boffile,
        self.fpga.progdev(self.boffile)
        print 'done'
    
    def set_gain(self):
        """
        Set the gain of all channels.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : int
            Channel gain. Uses the same gain for every channel.
        """
        
        # EQ SCALING!
        # writes only occur when the addr line changes value. 
        # write blindly - don't bother checking if write was successful. Trust in TCP!
        print 'Setting gains of all channels on all inputs to %i...' % self.gain,
        self.fpga.write_int('quant0_gain', self.gain) # write the same gain for all inputs, all channels
        self.fpga.write_int('quant1_gain', self.gain) # write the same gain for all inputs, all channels
        for chan in xrange(1024):
            #print '%i...'%chan,
            sys.stdout.flush()
            for input in xrange(2):
                self.fpga.blindwrite('quant%i_addr' % input, struct.pack('>I', chan))
        print 'done'
    
    def _set_acc_len(self, acc_len):
        """
        Sets the number of spectra to accumulate before output.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : int
            Number of spectra to accumulate before output.
        """
        
        print 'Configuring accumulation period...',
        self.fpga.write_int('acc_len', acc_len)
        print 'done'
    
    def set_coarse_delay(self, antenna, delay):
        """
        Changes the fringe tracking correction.
        Delay is in FPGA clock cycles.
        Antenna can be 0 or 1 for ARI.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : int
            Antenna number, 0 or 1 for ARI.
        var3 : int
            Coarse delay value in clock cycles.
        """
        
        print 'Configuring coarse delay...',
        print 'applying a delay of %i clock cycles to antenna %i...' % (delay, antenna),
        try:
            self.fpga.write_int('delay_ant%i' % antenna, delay)
        except RuntimeError:
            print 'Could not write to FPGA.'
        print 'done'
    
    def _set_fft_shift(self, shift=(2**32)-1):
        print 'Configuring fft_shift...',
        self.fpga.write_int('fft_shift', shift)
        print 'done'
        
    def set_file_name(self, _filename, product=None):
        #print "Set file name: existent output file %s will be updated to %s" % (self.filename, _filename)
        if product == 'ab':
            self.filename_ab = _filename
        elif product == 'ba':
            self.filename_ba = _filename
        elif product == 'aa':
            self.filename_aa = _filename
        elif product == 'bb':
            self.filename_bb = _filename
        elif not product:
            self.filename_ab = "{0}_ab".format(_filename)
            self.filename_ba = "{0}_ba".format(_filename)
            self.filename_aa = "{0}_aa".format(_filename)
            self.filename_bb = "{0}_bb".format(_filename)
    
    def get_data_cross(self, baseline):
        """
        Reads the crosscorrelation data from the FPGA.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : str
            Baseline name. ARI only has an ab baseline
        """
        
        acc_num = self.fpga.read_uint('acc_num')
        print 'Grabbing integration number %i' % acc_num
        self.acc_num = acc_num

        #get the data...
        baseline = 'ab'
        
        a_0r = struct.unpack('>512l', self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        a_1r = struct.unpack('>512l', self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))
        b_0r = struct.unpack('>512l', self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        b_1r = struct.unpack('>512l', self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))
        a_0i = struct.unpack('>512l', self.fpga.read('dir_x0_%s_imag'%baseline, 2048, 0))
        a_1i = struct.unpack('>512l', self.fpga.read('dir_x1_%s_imag'%baseline, 2048, 0))
        b_0i = struct.unpack('>512l', self.fpga.read('dir_x0_%s_imag'%baseline, 2048, 0))
        b_1i = struct.unpack('>512l', self.fpga.read('dir_x1_%s_imag'%baseline, 2048, 0))

        self.amp_ab = []
        self.amp_ba = []
        self.freq = []

        for i in xrange(512):
            self.amp_ab.append(complex(a_0r[i], a_0i[i]))
            self.amp_ab.append(complex(a_1r[i], a_1i[i]))
            self.amp_ba.append(complex(b_0r[i], b_0i[i]))
            self.amp_ba.append(complex(b_1r[i], b_1i[i]))
            self.freq.append(i*self.chw)
            
        self.amp_ab = numpy.array(self.amp_ab)
        self.amp_ba = numpy.array(self.amp_ba)
        self.freq = numpy.array(self.freq)

        return acc_num, self.freq, self.amp_ab, self.amp_ba

    def get_data_auto(self):
        """
        Reads the autocorrelation data from the FPGA.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        
        Return
        ------
        accumulation number, frequency, auto correlation antenna A, auto correlation antenna B
        """
        
        acc_num = self.fpga.read_uint('acc_num')
        print 'Grabbing integration number %i' % acc_num
        self.acc_num = acc_num

        baseline = 'aa'
        a_0 = struct.unpack('>512l', self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        a_1 = struct.unpack('>512l', self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))
        baseline = 'bb'
        b_0 = struct.unpack('>512l', self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        b_1 = struct.unpack('>512l', self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))

        self.amp_a = []
        self.amp_b = []
        self.freq = []

        for i in xrange(512):
            self.amp_a.append(a_0[i])
            self.amp_a.append(a_1[i])
            self.amp_b.append(b_0[i])
            self.amp_b.append(b_1[i])
            self.freq.append(i*self.chw)
        
        self.amp_a = numpy.array(self.amp_a)
        self.amp_b = numpy.array(self.amp_b)
        self.freq = numpy.array(self.freq)

        return acc_num, self.freq, self.amp_a, self.amp_b
    
    def get_spectrum(self):
        """
        Grabs both auto and cross correlation data.
        It does not guarantee that they correspond to
        the same integration.
        """
        
        a_n, a_freq, a_amp_a, a_amp_b = self.get_data_auto()
        c_n, c_freq, c_amp_ab, c_amp_ba = self.get_data_cross('ab')

        
    def write_spectrum(self, az1, el1, oaz1, oel1, az2, el2, oaz2, oel2):
        """
        Writes trace to file. One file per real number.
        Auto correlations are stored in separate files.
        Cross correlations are stored in 4 files, one for each product, and
        for each product one for real part, one for imag part.
        """
        
        if not self.datafile_aa:
            self.datafile_aa = open(self.filename_aa, 'a')
        if not self.datafile_bb:
            self.datafile_bb = open(self.filename_bb, 'a')
        if not self.datafile_abr:
            self.datafile_abr = open(self.filename_abr, 'a')
        if not self.datafile_abi:
            self.datafile_abi = open(self.filename_abi, 'a')
        if not self.datafile_bar:
            self.datafile_bar = open(self.filename_bar, 'a')
        if not self.datafile_bai:
            self.datafile_bai = open(self.filename_bai, 'a')
            
        #print "Writting data to %s ..." % self.filename_aa
        
        self.datafile_aa.write( arc_head(self.amp_a, az1, el1, oaz1, oel1,
                                         az2, el2, oaz2, oel2, self.freq[0], 
                                         self.get_chw(), self.fft, self.acc_num) )
        self.datafile_bb.write( arc_head(self.amp_b, az1, el1, oaz1, oel1,
                                         az2, el2, oaz2, oel2, self.freq[0], 
                                         self.get_chw(), self.fft, self.acc_num) )
        self.datafile_abr.write( arc_head(self.amp_ab.real, az1, el1, oaz1, oel1,
                                          az2, el2, oaz2, oel2, self.freq[0], 
                                          self.get_chw(), self.fft, self.acc_num) )
        self.datafile_abi.write( arc_head(self.amp_ab.imag, az1, el1, oaz1, oel1,
                                          az2, el2, oaz2, oel2, self.freq[0], 
                                          self.get_chw(), self.fft, self.acc_num) )
        self.datafile_bar.write( arc_head(self.amp_ba.real, az1, el1, oaz1, oel1,
                                          az2, el2, oaz2, oel2, self.freq[0], 
                                          self.get_chw(), self.fft, self.acc_num) )
        self.datafile_bai.write( arc_head(self.amp_ba.imag, az1, el1, oaz1, oel1,
                                          az2, el2, oaz2, oel2, self.freq[0], 
                                          self.get_chw(), self.fft, self.acc_num) )

        print "ready."


#!/usr/bin/env python
'''
This module provides functions to program and interact with a pocket correlator on a ROACH board.
It uses the Python KATCP library along with the katcp_wrapper distributed in the corr package. 
This is based on the script created by Jason Manley for the CASPER workshop.
It was modified to fit the requirements of ARI and its correlator.
Author: Jason Manley
Modified: Pedro Salas, July 2014.
'''

from __future__ import division

import sys
import corr
import time
import numpy
import struct
import logging
import datetime
import valon_synth as vs
import arc_params as arcp
    
def format_line(head, data, 
                fmt=( '%Y-%m-%d-%H-%M-%S.%f {head} data: {data} \r\n' )):
   
    data_line = datetime.datetime.now().\
                strftime(fmt).format(head=" ".join([str(h) for h in head]),
                                     data=" ".join([str(x) for x in data]),)
                                     
    return data_line
        

class ARCManager():
    
    def __init__(self, bw=100e6, chw=97656.25, fft=1024, gain=1000, 
                 acc_len=2**28/1024, log_handler=None, ip=arcp.roach_ip, 
                 synth=True):

        # Opens the Valon 5007 dual synth
        # SYNTH_B is the ADC clock, SYNTH_A the LO
        self.synth = synth
        if synth:
            self.synth = vs.Synthesizer(arcp.synth_port)
        
        # Connect to ROACH
        self.ip = ip
        self.log_handler = self._init_log(self.ip)
        self.fpga = self._connect_roach(arcp.katcp_port)
    
        # Sets configuration parameters while checking some
        self.head = []
        self.fft = fft
        self.bw = bw
        self.set_bw(bw)        
        self.num_channel = fft # to duplicate SHManager
        self.chw = chw
        self.set_chw(chw)
        self.lo_freq = 1370  # LO frequency in MHz
        self.set_LO(self.lo_freq)
        self.fc = 1420 - self.lo_freq
        self.gain = gain
        self.acc_time = 0
        self.acc_len = acc_len
        self.acc_num = 0
        self.tdump = 0
        self.clck = self.bw/4.0
        self.cdelay = 0
        
        # Writes firmware configuration to ROACH board
        self.boffile = self._config_to_boffile()
        self._set_bof_file()
        self._reset_firmware()
        self._set_fft_shift()
        self._set_acc_len(self.acc_len)
        self._set_gain()
        self.set_coarse_delay(0, self.cdelay)
        self.set_coarse_delay(1, self.cdelay)
        
        # Sets io detector parameters
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
        self.amp_ab = numpy.empty(self.fft)
        self.amp_ba = numpy.empty(self.fft)
        self.amp_a = numpy.empty(self.fft)
        self.amp_b = numpy.empty(self.fft)
        
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
            print ('No synthesizer on ROACH.'
                   'The LO frequency can not be changed.')
        else:
            self.synth.set_frequency(vs.SYNTH_A, lofreq)
            
    def set_ref_clck(self, adcfreq):
        """
        Specifies reference signal frequency for the ADC.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        var2 : ADC reference frequency
            Frequency in MHz.
        """
        if not self.synth:
            print ('No synthesizer on ROACH.'
                   'The ADC reference frequency can not be changed.')
        else:
            self.synth.set_frequency(vs.SYNTH_B, adcfreq)
    
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
        
        if bw not in arcp.allowed_config.keys():
            bw = 100e6
            print ('Bandwidth not yet implemented.' 
                   'Using default of %0.f MHz.') % bw
        self.set_ref_clck(2*self.bw/1e6)
        self.bw = bw
        self._update_boffile()
        
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
        if chw not in arcp.allowed_config[self.bw]:
            fft = 1024
            chw = arcp.allowed_config[self.bw][0]
            print ('Channel width not implemented.' 
                   'Using default of %0.f kHz') % chw
        self.chw = chw
        self.fft = int(fft)
        self.amp_ab = numpy.empty(self.fft)
        self.amp_ba = numpy.empty(self.fft)
        self.amp_a = numpy.empty(self.fft)
        self.amp_b = numpy.empty(self.fft)
        self._update_boffile()
    
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
        self._set_bof_file()
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
        fpga = corr.katcp_wrapper.FpgaClient(self.ip, katcp_port, 
                                             timeout=10, 
                                             logger=self.log_handler)
        time.sleep(1)
        
        if fpga.is_connected():
            print 'ok\n'
        else:
            print ('ERROR connecting to server' 
                   '%s on port %i.\n') % (arcp.roach_ip, katcp_port)
            self.exit_fail(self.log_handler)
        
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
        
    def _reset_firmware(self):
        """
        Resets the correlator firmware counters and triggers.
        """
        
        print ('Resetting board, software triggering'
               ' and resetting error counters...'),
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
    
    def _set_gain(self):
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
        # write blindly - don't bother checking if write was successful. 
        # Trust in TCP!
        print ('Setting gains of all channels '
                'on all inputs to %i...') % self.gain,
        # Use the same gain for all inputs, all channels
        self.fpga.write_int('quant0_gain', self.gain) 
        self.fpga.write_int('quant1_gain', self.gain)
        for chan in xrange(self.fft):
            #print '%i...'%chan,
            sys.stdout.flush()
            for input in xrange(2):
                self.fpga.blindwrite('quant%i_addr' % input, 
                                     struct.pack('>I', chan))
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
        print ('applying a delay of '
              '%i clock cycles to antenna %i...') % (delay, antenna),
        try:
            self.fpga.write_int('delay_ant%i' % antenna, delay)
            self.cdelay = delay
        except RuntimeError:
            print 'Could not write to FPGA.'
        print 'done'
    
    def _set_fft_shift(self, shift=(2**32)-1):
        print 'Configuring fft_shift...',
        self.fpga.write_int('fft_shift', shift)
        print 'done'
        
    def set_file_name(self, _filename, product=None):
        #print "Set file name: existent output file %s will be updated to %s" % (self.filename, _filename)
        if product == 'abr':
            self.filename_abr = _filename
        if product == 'abi':
            self.filename_abi = _filename
        elif product == 'bar':
            self.filename_bar = _filename
        elif product == 'bai':
            self.filename_bai = _filename
        elif product == 'aa':
            self.filename_aa = _filename
        elif product == 'bb':
            self.filename_bb = _filename
        elif not product:
            self.filename_abr = '{0}_abr'.format(_filename)
            self.filename_bar = '{0}_bar'.format(_filename)
            self.filename_abi = '{0}_abi'.format(_filename)
            self.filename_bai = '{0}_bai'.format(_filename)
            self.filename_aa = '{0}_aa'.format(_filename)
            self.filename_bb = '{0}_bb'.format(_filename)
    
    def get_data_cross(self, baseline='ab'):
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

        # get the data...
        a_0r = struct.unpack('>512l', 
                             self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        a_1r = struct.unpack('>512l', 
                             self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))
        b_0r = struct.unpack('>512l', 
                             self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        b_1r = struct.unpack('>512l', 
                             self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))
        a_0i = struct.unpack('>512l', 
                             self.fpga.read('dir_x0_%s_imag'%baseline, 2048, 0))
        a_1i = struct.unpack('>512l', 
                             self.fpga.read('dir_x1_%s_imag'%baseline, 2048, 0))
        b_0i = struct.unpack('>512l', 
                             self.fpga.read('dir_x0_%s_imag'%baseline, 2048, 0))
        b_1i = struct.unpack('>512l', 
                             self.fpga.read('dir_x1_%s_imag'%baseline, 2048, 0))

        self.amp_ab = []
        self.amp_ba = []

        for i in xrange(self.fft//2):
            self.amp_ab.append(complex(a_0r[i], a_0i[i]))
            self.amp_ab.append(complex(a_1r[i], a_1i[i]))
            self.amp_ba.append(complex(b_0r[i], b_0i[i]))
            self.amp_ba.append(complex(b_1r[i], b_1i[i]))
            
        self.amp_ab = numpy.array(self.amp_ab)
        self.amp_ba = numpy.array(self.amp_ba)

        return self.acc_num, self.amp_ab, self.amp_ba

    def get_data_auto(self):
        """
        Reads the autocorrelation data from the FPGA.
        
        Parameters
        ----------
        var1 : ARCManager
            self
        
        Return
        ------
        accumulation number, frequency, 
        auto correlation antenna A, 
        auto correlation antenna B
        """
        
        acc_num = self.fpga.read_uint('acc_num')
        print 'Grabbing integration number %i' % acc_num
        self.acc_num = acc_num

        baseline = 'aa'
        a_0 = struct.unpack('>512l', 
                            self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        a_1 = struct.unpack('>512l', 
                            self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))
        baseline = 'bb'
        b_0 = struct.unpack('>512l', 
                            self.fpga.read('dir_x0_%s_real'%baseline, 2048, 0))
        b_1 = struct.unpack('>512l', 
                            self.fpga.read('dir_x1_%s_real'%baseline, 2048, 0))

        self.amp_a = []
        self.amp_b = []
        self.freq = []

        for i in xrange(self.fft//2):
            self.amp_a.append(a_0[i])
            self.amp_a.append(a_1[i])
            self.amp_b.append(b_0[i])
            self.amp_b.append(b_1[i])
        
        self.amp_a = numpy.array(self.amp_a)
        self.amp_b = numpy.array(self.amp_b)

        return self.acc_num, self.amp_a, self.amp_b
    
    def get_spectrum(self):
        """
        Grabs both auto and cross correlation data.
        It does not guarantee that they correspond to
        the same integration.
        """
        
        a_n, a_amp_a, a_amp_b = self.get_data_auto()
        c_n, c_amp_ab, c_amp_ba = self.get_data_cross('ab')

        
    def write_spectrum(self):
        """
        Writes trace to file. One file per real number.
        Auto correlations are stored in separate files.
        Cross correlations are stored in 4 files, one for each product, and
        for each product one for real part and one for imag part.
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
            
        
        self.datafile_aa.write( format_line(self.head, self.amp_a) )
        self.datafile_bb.write( format_line(self.head, self.amp_b) )
        self.datafile_abr.write( format_line(self.head, self.amp_ab.real) )
        self.datafile_abi.write( format_line(self.head, self.amp_ab.imag) )
        self.datafile_bar.write( format_line(self.head, self.amp_ba.real) )
        self.datafile_bai.write( format_line(self.head, self.amp_ba.imag) )

        print "ready."
        
    def get_tdump(self):
        """
        Asks the ROACH for the data dump
        rate.
        """
        # factor 4 arises because the FFT processes 4 inputs simultaneously
        tdump = self.fft*self.acc_len/self.clck/4.0
        self.tdump = tdump
        return self.tdump
        
    def make_head(self, ant1=None, ant2=None, source=None):
        """
        Creates a list with observation data.
        The list is written at the beginning of
        each line in the output spectra.
        """
        
        minhead = ['fc', self.fc, 'bw', self.bw, 
                   'chw', self.chw, 'chnum', self.num_channel, 
                   'inum', self.acc_num, 'cdelay', self.cdelay]
    
        if source and ant1 and ant2:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow, 
                        'ant2_az', ant2.aznow, 'ant2_el', ant2.elnow,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num, 'cdelay', self.cdelay]
            except AttributeError:
                print 'Header keyword not found, using minimum header.'
                head = minhead

        elif source and ant1:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num, 'cdelay', self.cdelay]
            except AttributeError:
                print 'Header keyword not found, using minimum header.'
                head = minhead
                        
        elif ant1:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num, 'cdelay', self.cdelay]
            except AttributeError:
                print 'Header keyword not found, using minimum header.'
                head = minhead

        else:
            head = minhead

        self.head = head

        return head
        
    def exit_clean(self):
        """
        Stops the FPGA
        """
        try:
            self.fpga.stop()
        except: pass
        sys.exit()
        
    def exit_fail(self, log_handler=None):
        if log_handler:
            print 'FAILURE DETECTED. Log entries:\n', log_handler.printMessages()
        else:
            print 'FAILURE DETECTED.\n'
        try:
            fpga.stop()
        except: pass
        raise
        sys.exit()

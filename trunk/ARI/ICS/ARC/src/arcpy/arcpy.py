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
#import arc_params as arcp

__docformat__ = 'reStructuredText'

def nearest_value(value, array):
    """
    Returns the closest array element to the specified value.
    """
    
    try:
        nearest = array[abs(array - value).argmin()]
    except TypeError:
        nearest = array[abs(numpy.array(array) - value).argmin()]
    
    return nearest
 
def format_line(head, data, 
                fmt=( '%Y-%m-%d-%H-%M-%S.%f {head} data: {data} \r\n' )):
    """
    Concatenated the header and the data in a single string.
    This is based on the original MIT SRT java software output.
    """
   
    data_line = datetime.datetime.now().\
                strftime(fmt).format(head=" ".join([str(h) for h in head]),
                                     data=" ".join([str(x) for x in data]),)
                                     
    return data_line
        

class ARCManager():
    """
    Class used to manage an Academic Radio Correlator (ARC).
    """
    
    allowed_config = {100e6:[97656.25, 48828.125, 24414.0625],
                      400e6:[390625.0]}
    katcp_port = 7147
    roach_ip = '146.155.121.6'
    
    def __init__(self, bw=100e6, chw=97656.25, fft=1024, gain=1000, 
                 acc_len=(2**28)/1024, log_handler=None, ip='146.155.121.6', 
                 synth=True, synth_port='/dev/ttyUSB0'):
        
        """
        Creates an ARCManager object.
        
        Parameters
        ----------
        :param bw: Detector bandwidth.
        :param chw: Detector channel spacing.
        :param fft: FFT size. must be compatible with the bandwidth and channel spacing.
        :param gain: Gain factor. Each channel amplitude is multiplied by this value.
        :param acc_len: Number of spectra to accumulate in one integration.
        :param log_handler: Log handler used to store error messages.
        :param ip: Ip of the ROACH board. **SRT control room**: 146.155.121.6. **AIUC**:146.155.21.32
        :param synth: True if the syntheziser is connected to a control PC with the USB cable. False otherwise.
        :param synth_port: port where the syntheziser is mounted.
        :type bw: int, float
        :type chw: int, float
        :type fft: int, float
        :type gain: int
        :type acc_len: int
        :type log_handler: Logger object
        :type ip: string
        :type synth: bool
        :type synth_port: string
        """

        # Opens the Valon 5007 dual synth
        # SYNTH_B is the ADC clock, SYNTH_A the LO
        self.synth = synth
        if synth:
            self.synth = vs.Synthesizer(synth_port)
        
        # Connect to ROACH
        self.ip = ip
        self.log_handler = self._init_log(self.ip)
        self.fpga = self._connect_roach(self.katcp_port)
    
        # Sets configuration parameters
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
        self.acc_time = 0
        self.acc_len = acc_len
        self.acc_num = 0
        self.tdump = 0
        self.clck = self.bw/4.0
        self.cdelay = 0
        self.gain = gain
        
        # Writes firmware configuration to ROACH board
        self.boffile = self._config_to_boffile()
        self._set_bof_file()
        self._set_fft_shift()
        self._set_acc_len(self.acc_len)
        self._reset_firmware()
        self._set_gain(gain)
        self.set_coarse_delay(0, self.cdelay)
        self.set_coarse_delay(1, self.cdelay)
        
        # Sets io detector parameters
        # Separate real from imag output
        data_date = time.strftime("%Y%m%d-%H%M")
        self.filename_abr = data_date + '_abr'
        self.filename_bar = data_date + '_bar'
        self.filename_abi = data_date + '_abi'
        self.filename_bai = data_date + '_bai'
        self.filename_aa = data_date + '_aa'
        self.filename_bb = data_date + '_bb'
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
        
    def close_files(self):
        """
        Closes the files where the spectra is being written to.
        """
        
        if self.datafile_aa != None:
            self.datafile_aa.close()
        if self.datafile_bb != None:
            self.datafile_bb.close()
        if self.datafile_abr != None:
            self.datafile_abr.close()
        if self.datafile_abi != None:
            self.datafile_abi.close()
        if self.datafile_bar != None:
            self.datafile_bar.close()
        if self.datafile_bai != None:
            self.datafile_bai.close()
        
    def _config_to_boffile(self):
        """
        Outputs the .bof filename for a given bw and fft.
        """
        
        # Bandwidth is given in MHz in the .bof file names
        return 'arc_%d_%d.bof' % (self.bw/1e6, self.fft)
    
    def exit_clean(self):
        """
        Stops the FPGA.
        """
        
        try:
            self.fpga.stop()
        except: pass
        sys.exit()
        
    def exit_fail(self, log_handler=None):
        """
        Stops the FPGA with an error message.
        """
        
        if log_handler:
            print 'FAILURE DETECTED. Log entries:\n', log_handler[0].printMessages()
        else:
            print 'FAILURE DETECTED.\n'
        try:
            fpga.stop()
        except: pass
        raise
        sys.exit()
    
    def _update_boffile(self):
        """
        Sets the FPGA bof file based on the current ARC configuration.
        """
        
        self.boffile = self._config_to_boffile()
        print 'Changing current .bof file to %s...' % self.boffile,
        self._set_bof_file()
        print '... done.'

    def get_chw(self):
        """
        Returns the current channel width.
        
        Return
        ------
        ARC channel width in Hz.
        """
        
        print 'Using a channel width of %.0f' % self.chw
        return self.chw
    
    def get_bw(self):
        """
        Returns the current band width.
        
        Return
        ------
        ARC bandwidth in Hz.
        """
        
        print 'Using a band width of %.0f' % self.bw
        return self.bw
        
    def _connect_roach(self, katcp_port=7147):
        """
        Connects to a ROACH board through katcp_port using the corr
        module.
        
        Parameters
        ----------
        :param katcp_port: Port on the ROACH board to connect to.
        
        Return
        ------
        An FPGA object from the corr module.
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
                   '%s on port %i.\n') % (self.roach_ip, katcp_port)
            self.exit_fail(self.log_handler)
        
        return fpga
        
    def _init_log(self, ip):
        """
        Initializes the event log.
        
        Parameters
        ----------
        :param ip: ROACH ip.
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
        
    def _set_acc_len(self, acc_len):
        """
        Sets the number of spectra to accumulate before output.
        
        Parameters
        ----------
        :param acc_len: Number of spectra to accumulate before output.
        :type acc_len: int
        """
        
        print 'Configuring accumulation period...',
        self.fpga.write_int('acc_len', acc_len)
        self.acc_len = acc_len
        print 'done'
    
    def _set_bof_file(self):
        """
        Loads a .bof file into the FPGA.
        """
        
        print 'Programming FPGA with %s...' % self.boffile,
        self.fpga.progdev(self.boffile)
        print 'done'
        
    def set_bw(self, bw):
        """
        Sets the FPGA band width.
        This will update the channel width to the
        closest one allowed for this bandwidth.
        
        Parameters
        ----------
        :param bw: Band width. 100 MHz or 400 MHz.
        """
        
        if bw not in self.allowed_config.keys():
            bw = nearest_value(bw, self.allowed_config.keys())
            #bw = 100e6
            print ('Bandwidth not yet implemented. ' 
                   'Using default of %0.2f MHz.') % (bw/1e6)
        self.set_ref_clck(2*bw/1e6)
        self.bw = bw
        
    def set_chw(self, chw):
        """
        Sets the FPGA channel width.
        The channel width will change
        with each band width change.
        
        Parameters
        ----------
        :param chw: Channel width. Must be an allowed value.
        :type chw: float
        """
        
        fft = int(self.bw/chw)
        
        # Check if there is a .bof file for the requested configuration
        if chw not in self.allowed_config[self.bw]:
            chw = nearest_value(chw, self.allowed_config[self.bw])
            fft = int(self.bw/chw)
            #chw = self.allowed_config[self.bw][0]
            print ('Channel width not implemented. ' 
                   'Using default of %0.6f kHz') % (chw/1e3)
            
        self.chw = chw
        self.fft = int(fft)
        self.amp_ab = numpy.empty(self.fft)
        self.amp_ba = numpy.empty(self.fft)
        self.amp_a = numpy.empty(self.fft)
        self.amp_b = numpy.empty(self.fft)
    
    def set_coarse_delay(self, antenna, delay):
        """
        Changes the fringe tracking correction.
        Delay is in FPGA clock cycles.
        Antenna can be 0 or 1 for ARI.
        
        Parameters
        ----------
        :param antenna: Which antenna the delay is applied to. 
        :type antenna: int
        :param delay: Coarse delay to be applied. It should have units of clock cycles. 
        :type delay: int
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
        
    def set_file_name(self, filename, product=None):
        """
        Sets the name of the files that will contain the spectra.
        
        Parameters
        ----------
        :param filename: name of the output files.
        :type filename: string
        :param product: product to rename. By default all products output will be renamed.
                        The allowed values are: abr, abi, bar, bai, aa or bb.
        """
        #print "Set file name: existent output file %s will be updated to %s" % (self.filename, _filename)
        if product == 'abr':
            self.filename_abr = filename
        if product == 'abi':
            self.filename_abi = filename
        elif product == 'bar':
            self.filename_bar = filename
        elif product == 'bai':
            self.filename_bai = filename
        elif product == 'aa':
            self.filename_aa = filename
        elif product == 'bb':
            self.filename_bb = filename
        elif not product:
            self.filename_abr = '{0}_abr'.format(filename)
            self.datafile_abr = None
            self.filename_bar = '{0}_bar'.format(filename)
            self.datafile_bar = None
            self.filename_abi = '{0}_abi'.format(filename)
            self.datafile_abi = None
            self.filename_bai = '{0}_bai'.format(filename)
            self.datafile_bai = None
            self.filename_aa = '{0}_aa'.format(filename)
            self.datafile_aa = None
            self.filename_bb = '{0}_bb'.format(filename)
            self.datafile_bb = None
    
    def _set_gain(self, gain):
        """
        Set the gain of all channels.
        
        Parameters
        ----------
        :param gain: Channel gain. Uses the same gain for every channel.
        :type gain: int
        """
        
        # EQ SCALING!
        # writes only occur when the addr line changes value. 
        # write blindly - don't bother checking if write was successful. 
        # Trust in TCP!
        self.gain = gain
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
    
    def set_LO(self, lofreq):
        """
        Specifies LO frequency.
        
        Parameters
        ----------
        :param lofreq: LO frequency in MHz.
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
        :param adcfreq: ADC reference frequency in MHz.
        """
        
        if not self.synth:
            print ('No synthesizer on ROACH.'
                   'The ADC reference frequency can not be changed.')
        else:
            self.synth.set_frequency(vs.SYNTH_B, adcfreq)
    
    def start(self, ip='146.155.121.6'):
        """
        Starts the FPGA.
        """
        
        # Connect to ROACH
        self.ip = ip
        self.log_handler = self._init_log(self.ip)
        self.fpga = self._connect_roach(self.katcp_port)
    
    def stop(self):
        """
        Stops the FPGA.
        """
        
        self.exit_clean()
        
    
    def getData(self):
        """
        Stores the current accumulation into the ARCManager variables.
        
        Return
        ------
        4 numpy arrays containing the data.
        ab, ba, aa, bb
        The first 2 contain complex numbers.
        """
        
        self.get_spectrum()
        
        return self.amp_ab, self.amp_ba, self.amp_a, self.amp_b
    
    def get_data_cross(self, baseline='ab'):
        """
        Reads the crosscorrelation data from the FPGA.
        
        Parameters
        ----------
        :param baseline: Baseline name. ARI only has an ab baseline.
        :type baseline: string
        """
        
        acc_num = self.fpga.read_uint('acc_num')
        print 'Grabbing integration number %i' % acc_num
        self.acc_num = acc_num

        # Minimum BRAM size is 2048
        if self.fft < 2048:
            fft = 2048
            rfft = 512
        else:
            fft = self.fft*2
            rfft = self.fft//2
            
        # get the data...
        a_0r = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x0_%s_real'%baseline, fft, 0))
        a_1r = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x1_%s_real'%baseline, fft, 0))
        b_0r = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x0_%s_real'%baseline, fft, 0))
        b_1r = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x1_%s_real'%baseline, fft, 0))
        a_0i = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x0_%s_imag'%baseline, fft, 0))
        a_1i = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x1_%s_imag'%baseline, fft, 0))
        b_0i = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x0_%s_imag'%baseline, fft, 0))
        b_1i = struct.unpack('>{0:d}l'.format(rfft), 
                             self.fpga.read('dir_x1_%s_imag'%baseline, fft, 0))

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
        
        Return
        ------
        accumulation number, frequency, 
        auto correlation antenna A, 
        auto correlation antenna B
        """
        
        acc_num = self.fpga.read_uint('acc_num')
        print 'Grabbing integration number %i' % acc_num
        self.acc_num = acc_num

        # Minimum BRAM size is 2048
        if self.fft < 2048:
            fft = 2048
            rfft = 512
        else:
            fft = self.fft*2
            rfft = self.fft//2
        
        baseline = 'aa'
        a_0 = struct.unpack('>{0:d}l'.format(rfft),
                            self.fpga.read('dir_x0_%s_real'%baseline, fft, 0))
        a_1 = struct.unpack('>{0:d}l'.format(rfft), 
                            self.fpga.read('dir_x1_%s_real'%baseline, fft, 0))
        baseline = 'bb'
        b_0 = struct.unpack('>{0:d}l'.format(rfft), 
                            self.fpga.read('dir_x0_%s_real'%baseline, fft, 0))
        b_1 = struct.unpack('>{0:d}l'.format(rfft), 
                            self.fpga.read('dir_x1_%s_real'%baseline, fft, 0))

        self.amp_a = []
        self.amp_b = []

        for i in xrange(self.fft//2):
            #print i
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
        The spectrum is saved in the ARCManager internal 
        variables.
        """
        
        self.get_data_auto()
        self.get_data_cross('ab')
        
    def get_tdump(self):
        """
        Asks the ROACH for the data dump rate.
        
        Return
        ------
        The time it takes to process a spectrum in seconds.
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
        
        Return
        ------
        A list containing the header keywords and their respective values.
        """
        
        minhead = ['fc', self.fc, 'bw', self.bw, 
                   'chw', self.chw, 'chnum', self.num_channel, 
                   'inum', self.acc_num, 'acclen', self.acc_len]
    
        if source and ant1 and ant2:
            # added exception in case we want to migrate to a common
            # data handling module which writes headers or other data
            # that way we can have a common head writer, or whatnot.
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow,
                        'ant1_azoff', ant1.az_off, 'ant1_eloff', ant1.el_off,
                        'ant1_noise', ant1.noise,
                        'ant2_az', ant2.aznow, 'ant2_el', ant2.elnow,
                        'ant2_azoff', ant2.az_off, 'ant2_eloff', ant2.el_off,
                        'ant2_noise', ant2.noise,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num, 'acclen', self.acc_len,
                        'cdelay', self.cdelay]
            except AttributeError:
                print 'Header keyword not found, using minimum header.'
                head = minhead

        elif source and ant1:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow,
                        'ant1_azoff', ant1.az_off, 'ant1_eloff', ant1.el_off,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num, 'acclen', self.acc_len,
                        'cdelay', self.cdelay]
            except AttributeError:
                print 'Header keyword not found, using minimum header.'
                head = minhead
                        
        elif ant1:
            try:
                head = ['sou_az', source.az, 'sou_el', source.alt, 
                        'ant1_az', ant1.aznow, 'ant1_el', ant1.elnow,
                        'ant1_azoff', ant1.az_off, 'ant1_eloff', ant1.el_off,
                        'fc', self.fc, 'bw', self.bw, 
                        'chw', self.chw, 'chnum', self.num_channel, 
                        'inum', self.acc_num, 'acclen', self.acc_len,
                        'cdelay', self.cdelay]
            except AttributeError:
                print 'Header keyword not found, using minimum header.'
                head = minhead

        else:
            head = minhead

        self.head = head

        return head
        
    def take_data(self):
        """
        Fast way to take data
        """
        self.get_spectrum()
        self.make_head()
        self.write_spectrum()
        time.sleep(self.get_tdump())
        print "ready."
        
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

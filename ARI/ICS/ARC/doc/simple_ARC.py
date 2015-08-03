#!/usr/bin/env python

"""
Simple script that demonstrates how to create an ARC object
and record some spectra.
Author: Pedro Salas, salas.mz@gmail.com, July 2015.
"""

import arcpy

if __name__ == '__main__':
    
    # Create an ARCManager object,
    # specify the correlator configuration on startup to a 
    # bandwidth of 400 MHz and the default channel width of
    # ~390 kHz, which corresponds to 1024 channels.
    # Tell the ARCManager to connect to port 7147 on the ip 
    # 146.155.21.32, this is specific to the AIUC LAN.
    # Also, tell the ARCMAanager that we have control over
    # the Valon synthesizer card. The card is mounted in 
    # /dev/ttyUSB0, but this is /dev/valonsynth on the SRT
    # control PC.
    arc = arcpy.ARCManager(bw=400e6, 
                           chw=390000, 
                           fft=1024, 
                           ip='146.155.21.32', 
                           synth=True,
                           synth_port='/dev/ttyUSB0')
    
    # Set the base filename of the output spectra to example1.
    # The output files will be: 
    # example1_aa: auto-correlation from port I+
    # example1_bb: auto-correlation from port Q+
    # example1_abr: real part of the cross-correlation between I+ and Q+
    # example1_abi: imaginary part of the cross-correlation between I+ and Q+
    # example1_bar: same as example1_abr since the measured signal is real
    # example1_bai: same as example1_abi since the measured signal is real
    arc.set_file_name('example1')
    
    # Take one spectrum, both auto and cross correlations and write it to disk.
    arc.take_data()
    
    # Close the output files.
    # If not closed the last line of the files will be missing characters.
    arc.close_files()
    
    # After checking the recorded spectrum the observer determines that the spectral resolution
    # was not enough. The observer decides to use less bandwidth to increase the spectral resolution.
    # The observer also decides that there is too much RFI so he wants a faster integration time
    # to flag the RFI offline.
    # A new ARCManager object must be created. This ensures that all the triggers and counters
    # are set correctly.
    arc = arcpy.ARCManager(bw=100e6, 
                           chw=24000, 
                           fft=4096, 
                           ip='146.155.21.32', 
                           synth=True,
                           synth_port='/dev/ttyUSB0',
                           acc_len=2**20)
    
    # Set the filename again
    arc.set_file_name('example2')
    
    # Take 5 spectra
    for i in range(5):
        arc.take_data()
    
    # Close the output files
    arc.close_files()
    
    # Stop the gateware and close the connection
    arc.exit_clean()
    
    
    
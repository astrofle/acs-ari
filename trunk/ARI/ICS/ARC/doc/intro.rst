.. _introduction:

**************************************
What is the Academic Radio Correlator?
**************************************

.. _installing-docdir:

Correlator
============

A correlator is a piece of hardware that is able to perform the operation of 
multiplying and accumulating. In the case of a radio correlator, two radio 
signals are multiplied and their product accumulated for a given time.
This is equivalent to its mathematical definition
   
.. math::

    \int_{-\infty}^{\infty}f(t)g^{*}(t-\tau)dt
    
This is what the Academic Radio Correlator does under the hood.

ROACH
-----

ARC is a ROACH board configured as a digital correlator. This first digitizes the data using an Analog to Digital Converter (ADC) and then processes the data.
ARC is able to compensate for the coarse delay between signals. This is accomplished by shifting in time one of the signals an integer number of times. In practice this is done by storing one of the time streams in memory,
and then reading it when a defined time has elapsed. The remaining delay, the fine delay, has to be corrected by multiplying the signals by a complex number. This is not implemented inside ARC.

ARC uses the Poly Filter Bank technique to produce a spectrum. For this the signals in time domain are first multiplied by a window function and then the Fourier Transform of the time signal is 
computed producing a signal in frequency domain. The conversion of signal from time domain to frequency domain is known as the F operation.

After the F operation the correlator performs the X operation. This corresponds to multiplying the signals from different antennas and then accumulating the product before outputing a spectrum.

ARC configurations
------------------

ARC allows the use of the following configurations:

.. tabularcolumns:: |c|c|c|c|

===========  ========== ================= ===============
Bandwidth    PFB size   Number channels   Channel width
 (MHz)           2^                            (kHz)
===========  ========== ================= ===============
 400            11             1024            390
 100            11             1024            97.6
 100            12             2048            48.8
 100            13             4096            24.4
 100            14             8192            12.2
 100            15            16384            6.1
===========  ========== ================= ===============
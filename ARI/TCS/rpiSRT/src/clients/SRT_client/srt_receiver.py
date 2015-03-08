#attenuator control??? unknown
#if digital==0, receiver saturates at 3000 counts (attenuator neeeded)
#attenuator values : 0, 1 ,2
#if digital > 0 , receiver does not need attenuator, saturation at 50000 counts
import math
import random
import struct
import serial
import time
import matplotlib
matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt

import numpy as np
import threading

port = '/dev/ttyUSB0'
ser = serial.Serial(port, baudrate=2400, timeout = 10)

class Receiver:
	def __init__(self):
		self.slew = False
		self.noisecal = 0.0
		self.curvcorr = 0.0
		self.calcons = 1.0
		self.tload = 300.0
		self.tspill = 20.0
		self.beamw = 5.0
		self.pscale = 400.0
		self.fcenter = 1420.0 # default for continuum
		self.freqa = 1420.0
		self.restfreq = 1420.406 # se usa para calcular la velocidad en doppler H-Line rest freq
		self.nfreq = 1
		self.freqsep = 0.04
		self.intg = 0.1
		self.radiosim = 1 # simular receiver

		#simula receiver
		if self.radiosim:
			self.fcenter = 1420.4 #defaul for H-line
			self.nfreq = 40

		#If not simulation fcenter = 1420.0, nfreq = 1, freqsep = 0.04, intg = 0.1
		#If simulation fcenter = 1420.4, nfreq = 40
		self.receiver_default = '0a'
		self.tstart = 0
		self.tsys = 0.0
		self.stopproc = 0
		self.atten = 0
		self.calon = 0
		self.docal = 0
		self.sourn = 0
		self.track = 0
		self.scan = 0
		self.bsw = 0
		self.mancal = 0
		self.sig = 1
		self.specd = [0]*64
		self.rGraph = True
		#from config file (read *.cat)
		self.calcons = 0.1 # gain correction constant to put power in units of K */
		self.beamw = 7.0
		self.noisecal = 200.0
		self.digital = True
		#receiver configuration
		self.receivers = {
				'0':{'nfreq':500, 'freqsep':0.04, 'intg':0.1},
				'0a':{'nfreq':40, 'freqsep':0.04, 'intg':0.1},
				'1':{'nfreq':64, 'freqsep':0.0078125, 'intg':0.1},
				'1a':{'nfreq':64, 'freqsep':0.0078125,'intg':0.52488},
				'2':{'nfreq':64, 'freqsep':0.00390625, 'intg':1.04976},
				'3':{'nfreq':64, 'freqsep':0.001953125, 'intg':2.09952},
				'4':{'nfreq':156,'freqsep':0.0078125, 'intg':0.52488},
				'5':{'nfreq':40,'freqsep':1.0, 'intg':0.52488}
		}

		#receiver default initialization from *.cat 
		#(whenever the word digital is present in the cat file)
		#If not present no initialization is done
		if self.digital:
			self.receiver_default = '1a'
			self.receiver = self.receiver_default
			self.nfreq = self.receivers[self.receiver]['nfreq']
			self.freqsep = self.receivers[self.receiver]['freqsep']
			self.intg = self.receivers[self.receiver]['intg']

		if self.receiver != '0a':
			self.graycorr = [0]*64
			cf = [1.000000, 1.006274, 1.022177, 1.040125, 1.051102, 1.048860, 1.033074, 1.009606,
            0.987706, 0.975767, 0.977749, 0.991560, 1.009823, 1.022974, 1.023796, 1.011319,
            0.991736, 0.975578, 0.972605, 0.986673, 1.012158, 1.032996, 1.025913, 0.968784,
            0.851774, 0.684969, 0.496453, 0.320612, 0.183547, 0.094424, 0.046729, 0.026470,
            0.021300]
		for i in range(0,33):
			if (i < 32):
				self.graycorr[ i + 32]= cf[i];
			if (i < 33):
				self.graycorr[32 - i] = cf[i];

	def set_freq(self, new_fcenter, new_nfreq, new_freqsep, new_receiver):
	#set freq (fcenter, nfreq, freqsep, receiver)		
	#por comando se puede configurar el receiver
	#if receiver = 0|0a se puede configurar: fcenter, nfreq, freqsep
	#if receiver != 0|0a se puede configurar: fcenter, receiver
	#Si el receiver es digital:
	#if new receiver < 1 --> receiver = 1, 
	#if new receiver = 5 --> nfreq = 40, freqsep = 1.0, intg = 0.52488, luego 
	#	luego configura nfreq (nfreq_max = 500) y freqsep (freqsep_min = 1) si se ingresan
	#if new receiver < 5 se configura uno de los modos del 1a al 4 en receivers
		self.fcenter = new_fcenter
		if (new_nfreq < 1):
			new_nfreq = 1
		if (new_nfreq > 500):
			new_nfreq = 500
		if not(self.digital):
			self.nfreq = new_nfreq
			self.freqsep = new_freqsep
			self.receiver = '0a'
		else:
			if (int(new_receiver)<1):
				new_receiver = '1'
			self.receiver = str(new_receiver)
			if (int(new_receiver)==5):
				self.nfreq = 40
				self.freqsep = 1.0
				self.intg = 0.52488
				try:
					self.nfreq = new_nfreq
					self.freqsep = new_freqsep
				except:
					pass	
			else:
				self.nfreq = self.receivers[str(new_receiver)]['nfreq']
				self.freqsep = self.receivers[str(new_receiver)]['freqsep']
				self.intg = self.receivers[str(new_receiver)]['intg']
	
	def vane_calibration(self):
		self.atten = 0 # attenuator to 0 (not used for digital = True)
	

			
	def radiodg(self, freq):
		#freq in MHz
		self.avpower = 0
		self.power = 0
		self.a =0
		j = int(freq*(1.0/0.04)+0.5)
		mode = int(self.receiver[0]) - 1
		if (mode < 0 or mode == 4 or mode == 5):
			mode = 0
		b8 = (mode)
		b9 = (j & 0x3f)
		b10= ((j >> 6) & 0xff)
		b11= ((j >> 14) & 0xff)
		msg = struct.pack('b4s4b', 0, 'freq', b11, b10, b9, b8)
		self.freqa = (((b11*256.0 + (b10 & 0xff))*64.0 + (b9 & 0xff))*0.04 - 0.8)
		#Enviar comando por puerto serial y esperar respuesta en variable recv
		#simulacion#
		ser.write(msg)
		receiving = True
		while receiving:
			if ser.inWaiting() == 128:
				receiving = False
			else:
				pass
		data = ser.read(ser.inWaiting())
		recv = struct.unpack('64H', data)
		#####
		for i in range(64):
			if (i<=31):
				k = (i+32)
			else:
				k = (i-32)
			power = recv[k]
			if (int(self.receiver[0])<5):
				a = (i-32) * self.freqsep * 0.4
			else:
				a = 0
			if self.graycorr[i] > 0.8:
				power = power / (self.graycorr[i] * (1.0 + a * a * self.curvcorr))
			
			a = self.calcons * power
			if i>0:
				self.specd[64-i] = a
			else:
				self.specd[0] = a
			if (i>=10 and i<54):
				self.avpower += power
		
		self.avpower = self.avpower /44.0
		self.a = self.calcons * self.avpower
		print self.avpower, self.a

		
	def sim_spectrum(self):
		self.spectrum = [0]*128
		for i in range(64):
			power = 200.0 + self.tspill
			tsig = 100000.0 # Moon
			power += tsig
			power += power*self.gauss()/math.sqrt(self.freqsep*1e6*self.intg)
			power = power * self.graycorr[i]	
			if i<32:		
				self.spectrum[64+2*i] = power
				self.spectrum[64+2*i+1] = power
			else:
				self.spectrum[2*i-64] = power
				self.spectrum[2*i+1-64] = power
			#Enviar datos por puerta serial
			
	def gauss(self):
		r = 0.0
		while(r>1.0 or r==0.0):
			v1 = 2.0 * random.random() - 1.0
			v2 = 2.0 * random.random() - 1.0
			r = v1 * v1 + v2 * v2
		fac = math.sqrt(-2.0 * math.log(r) / r)
		vv1 = v1 * fac
		return vv1
		
	def initGraph(self):
		#plot initialization
		points = 64
		self.fig, self.ax = plt.subplots()
		self.line, = self.ax.plot(np.zeros(points))
		self.line1, = self.ax.plot(np.zeros(points))
		self.ax.set_autoscale_on(False)
		self.line.set_xdata(np.arange(points))
		#self.line1.set_xdata(self.f_target*np.ones(points))
		#self.line1.set_ydata(np.arange(float(points))/100)
		#self.ax.set_yscale('log')
		plt.axis([0, 63, 0, 6000])
		plt.grid(True)
		plt.show(block=False)

	def graph(self):
		#plot loop
		#the plot routine is intented to maximize plot speed
		#idea from 
		while(self.rGraph):
			self.line.set_ydata(self.specd)
			self.ax.draw_artist(self.ax.patch)
			self.ax.draw_artist(self.line)
			self.ax.draw_artist(self.line1)
			self.fig.canvas.update()
			self.fig.canvas.flush_events()
			time.sleep(0.2)

	def graph_thread(self):
		#plot thread
		graph_thread = threading.Thread(target = self.graph)
		graph_thread.start()
	
	def radiodg_thread(self, freq):
		if self.slew:
			print "wait until antenna stops slew"
		else:
			radiodg_thread = treading.Thread(target = self.radiodg, args=(freq))
			radiodg_thread.start()
		return	
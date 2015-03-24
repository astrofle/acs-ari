import math
import time
import matplotlib
matplotlib.use('QT4Agg')
import matplotlib.pyplot as plt
import threading
import csv
import numpy as np

class gspec():
	def __init__(self):
		self.rGraph = False
		
	def graph_thread(self):
		#plot thread
		graph_thread = threading.Thread(target = self.graph)
		graph_thread.start()
		
	def graph(self):
	#plot loop
	#the plot routine is intented to maximize plot speed
	#idea from 
		while(self.rGraph):
			try:
				f = open('fspec.csv','r')
				reader = csv.reader(f, delimiter=',')
				row = reader.next()
				sp1 = []
				for s in row:
					sp1.append(float(s))
				f.close()
					
				f = open('fspecd.csv','r')
				reader = csv.reader(f, delimiter=',')
				row = reader.next()
				sp2 = []
				for s in row:
					sp2.append(float(s))
				f.close()
				
				f = open('favspec.csv','r')
				reader = csv.reader(f, delimiter=',')
				row = reader.next()
				sp3 = []
				for s in row:
					sp3.append(float(s))
				f.close()
				
				f = open('favspecc.csv','r')
				reader = csv.reader(f, delimiter=',')
				row = reader.next()
				sp4 = []
				for s in row:
					sp4.append(float(s))
				f.close()
											
				self.line1.set_ydata(sp1)
				self.line2.set_ydata(sp2)
				self.line3.set_ydata(sp3)
				self.line4.set_ydata(sp4)												
				self.ax.draw_artist(self.ax.patch)
				#self.ax.draw_artist(self.line1)
				#self.ax.draw_artist(self.line2)
				#self.ax.draw_artist(self.line3)
				self.ax.draw_artist(self.line4)
				self.fig.canvas.update()
				self.fig.canvas.flush_events()
			except:
				pass
			time.sleep(1.0)
	
	def yscale(self, ymin, ymax):
		 plt.axis([0, 255, ymin, ymax])
	
	def initGraph(self):
		#plot initialization
		self.fig, self.ax = plt.subplots()
		self.line1, = self.ax.plot(np.zeros(256))
		self.line2, = self.ax.plot(np.zeros(256))
		self.line3, = self.ax.plot(np.zeros(256))
		self.line4, = self.ax.plot(np.zeros(256))
		self.ax.set_autoscale_on(True)
		self.line1.set_xdata(range(256))
		self.line2.set_xdata(range(256))
		self.line3.set_xdata(range(256))
		self.line4.set_xdata(range(256))
		#self.ax.set_yscale('log')
		plt.axis([0, 255, 0.0, 30000])
		plt.grid(True)
		plt.show(block=False)
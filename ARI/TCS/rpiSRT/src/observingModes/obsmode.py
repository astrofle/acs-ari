import sys
import time
sys.path.insert(0,'./SRT_client')
sys.path.insert(0,'./SH_client')
sys.path.insert(0,'./ROACH_client')

from SHControlClient import *
from ROACHControlClient import *
from SRTControlClient1 import *



class ARI_obsmodes():
	def __init__(self):
		self.ARI_nodes = {'SRT1':'192.168.0.6 -p 10000',
			'SRT2':'192.168.0.6 -p 10001',
			'SH':'192.168.0.6 -p 10002',
			'ROACH':'192.168.0.6 -p 10003'
			}
		pass

	def SRTAntennas(self):
		self.srt1 = SRT() # control for a single antenna
		self.srt1.setIP(self.ARI_nodes['SRT1'])
		self.srt1.connect()
		time.sleep(2)
		self.srt2 = SRT()
		self.srt2.setIP(self.ARI_nodes['SRT2'])
		self.srt2.connect()
		time.sleep(2)
		
	def SingleDishSRT(self, SRT_antenna):
		print "This is the Single Dish SRT Observing mode"
		self.srt = SRT() # control for a single antenna
		self.srt.setIP(self.ARI_nodes[SRT_antenna])
		self.srt.connect()

	def DoubleSingleDishSRT(self):
		print "This is the Double Single Dish SRT Observing mode"
		self.SRTAntennas()
	
				
	def ARI_SH(self):
		print "This is the ARI - Signal Hound Observing mode"
		self.SRTAntennas()
		self.sh = SH() # control for signal hound
		self.sh.setIP(self.ARI_nodes['SH'])
		self.sh.connect()
		self.sh.Message('hola')
		time.sleep(2)

	def ARI_ROACH(self):
		print "This is the ARI - ROACH Observing mode"
		self.SRTAntennas()
		roach = ROACH() # control for signal hound
		roach.connect()
		roach.Message('hola')
	
	def clean(self):
		try:
			self.srt1 = None
		except:
			pass
		try:
			self.srt2 = None
		except:
			pass
		try:
			self.SH = None
		except:
			pass
		try:
			self.ROACH = None
		except:
			pass
		


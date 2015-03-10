import sys, traceback, Ice
from time import sleep
import SHControl
#import SRT_control_lib_test as SRT
import threading
import os

class SHControlI(SHControl.SignalHound):
	def __init__(self):
		pass
	
	def message(self, s, current = None):
		print s
		return "I'm the Signal Hound, message received"

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
	#adapter = ic.createObjectAdapterWithEndpoints("SHController", "default -h 192.168.0.6 -p 10002")
	adapter = ic.createObjectAdapterWithEndpoints("SHController", IP)
	object = SHControlI()
	adapter.add(object, ic.stringToIdentity("SHController"))
	adapter.activate()
	print "SH Server up and running!"
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



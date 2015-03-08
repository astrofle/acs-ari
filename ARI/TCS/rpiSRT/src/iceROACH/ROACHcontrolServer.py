import sys, traceback, Ice
from time import sleep
import ROACHControl
#import SRT_control_lib_test as SRT
import threading
import os

class ROACHControlI(ROACHControl.ROACH):
	def __init__(self):
		pass
		
	def message(self, s, current = None):
		print s
		return "I'm the Roach, message received"

try:
	IP =  ' '.join(sys.argv[1:])
except:
	print "use ROACHcontrolServer.py default -h 192.168.0.6 -p 10003"
	sys.exit()
	
status = 0
ic = None
try:
	#ic = Ice.initialize(sys.argv)
	ic = Ice.initialize([''])
	#adapter = ic.createObjectAdapterWithEndpoints("ROACHController", "default -h 192.168.0.6 -p 10003")
	adapter = ic.createObjectAdapterWithEndpoints("ROACHController", IP)
	object = ROACHControlI()
	adapter.add(object, ic.stringToIdentity("ROACHController"))
	adapter.activate()
	print "ROACH Server up and running!"
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



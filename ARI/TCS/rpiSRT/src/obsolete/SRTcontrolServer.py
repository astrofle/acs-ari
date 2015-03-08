import sys, traceback, Ice
from time import sleep
import SRTControl

class SRTControlI(SRTControl.telescope):
	def SRTinit(self, s, current=None):
		sleep(1)
		print s

status = 0
ic = None
try:
	ic = Ice.initialize(sys.argv)
	adapter = ic.createObjectAdapterWithEndpoints("SRTController", "default -h 192.168.0.7 -p 10000")
	object = SRTControlI()
	adapter.add(object, ic.stringToIdentity("SRTController"))
	adapter.activate()
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



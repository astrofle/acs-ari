import sys, traceback, Ice
import SRTControl

#global variables
global status
global ic
global controller


ic = None

class MyCallback(object):
	def __init__(self):
		pass

	def getNameCB(self, a):
		print a

	def failureCB(self, ex):
		print "Exception is: " + str(ex)

class serialCallback(object):
	def __init__(self):
		pass
	
	def getNameCB(self, a):
		print a

	def failureCB(self, a):
		print a

	

def connect():
    global status
    global ic
    global controller

    status = 0

    try:
    	# Reading configuration info
		#configPath = os.environ.get("SWROOT")
		#configPath = configPath + "/config/LCU-config"
		initData = Ice.InitializationData()
		initData.properties = Ice.createProperties()
		initData.properties.load('IceConfig')
		ic = Ice.initialize(sys.argv, initData)
		# Create proxy
		base = ic.stringToProxy("SRTController:default -h 192.168.0.7 -p 10000")
		controller = SRTControl.telescopePrx.checkedCast(base)
		cb1 = MyCallback()
		controller.begin_message("connecting to controller", cb1.getNameCB, cb1.failureCB);
		print "Connected to SRTController"
		if not controller:
			raise RuntimeError("Invalid proxy")
    except:
    	traceback.print_exc()
    	status = 1
    	sys.exit(status)
    return

def disconnect():
    global status
    print "Disconnecting.."
    if ic:
        try:
            ic.destroy()
        except:
            traceback.print_exc()
            status = 1
            sys.exit(status)
    return

def GetSerialPorts():
	global status
	status = 0
	ic = None
	try:
		cb1 = MyCallback()
		#controller.begin_SRTinit("parametersV01", cb1.getNameCB, cb1.failureCB);
		controller.begin_SRTGetSerialPorts(cb1.getNameCB, cb1.failureCB);
		print "Ok"
	except:
		traceback.print_exc()
		status = 1
	return
	
def SetSerialPort(port):
	global status
	status = 0
	ic = None
	try:
		cb1 = MyCallback()
		controller.begin_SRTSetSerialPort(port, cb1.getNameCB, cb1.failureCB);
		print "Ok"
	except:
		traceback.print_exc()
		status = 1
	return
	
def SRTInit(parameters):
	global status
	status = 0
	ic = None
	try:
		cb1 = MyCallback()
		controller.begin_SRTinit(parameters, cb1.getNameCB, cb1.failureCB);
		print "loading parameters file and sending antenna to stow"
	except:
		traceback.print_exc()
		status = 1
	return
			
def SRTStow():
	global status
	status = 0
	ic = None
	try:
		cb1 = MyCallback()
		controller.begin_SRTStow(cb1.getNameCB, cb1.failureCB);
		print "sending antenna to stow"
	except:
		traceback.print_exc()
		status = 1
	return

def SRTStatus():
	global status
	status = 0
	ic = None
	try:
		cb1 = MyCallback()
		controller.begin_SRTStatus(cb1.getNameCB, cb1.failureCB);
		print "getting SRT status"
	except:
		traceback.print_exc()
		status = 1
	return

def SRTAzEl(az, el):
	global status
	status = 0
	ic = None
	try:
		cb1 = MyCallback()
		controller.begin_SRTAzEl(az, el, cb1.getNameCB, cb1.failureCB);
		print "moving the antenna"
	except:
		traceback.print_exc()
		status = 1
	return
			

			
if ic:
	#clean up
	try:
		ic.destroy()
	except:
		traceback.print_exc()
		status = 1



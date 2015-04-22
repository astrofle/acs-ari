#!/usr/bin/python 
import sys, traceback, Ice 
import ARIAPI
from datetime import datetime
import time
import os

#global variables
global status 
global ic 
global impl 

def connect():
    global status
    global ic
    global impl

    print "Connecting.."
    status = 0
    try:
        # Reading configuration info 
        configPath = os.environ.get("INTROOT")
        #print configPath
        #configPath = configPath + "/config/API-client.config"
        configPath = "./API-client.config"
        initData = Ice.InitializationData()
        initData.properties = Ice.createProperties()
        initData.properties.load(configPath)
        ic = Ice.initialize(sys.argv, initData)

        # Create proxy
        properties = ic.getProperties();
        proxyProperty = "APIAdapter.Proxy"
        proxy = properties.getProperty(proxyProperty);
        print "proxy=" + proxy
        obj = ic.stringToProxy(proxy);
        impl = ARIAPI.APIPrx.checkedCast(obj)
        print "Connected to ARI API Server"
        if not impl:
            raise RuntimeError("Invalid proxy")
    except:
       traceback.print_exc()
       status = 1
       sys.exit(status)

def disconnect():
    global status
    print "Desconnecting.."
    if ic:
        try: 
            ic.destroy()
        except:
            traceback.print_exc()
            status = 1
            sys.exit(status)

def sayHello():
    try:
        impl.sayHello()
        print "I said Hello!!"
    except:
        traceback.print_exc()
        status = 1

def getStatus():
    try:
        status = AIUC.APIStatus()
        print "Getting Status!!"
        status = impl.getStatus()
        print "Calibration Unit Status"
        print "lamp1    = %d " % status.lamp1
        print "lamp2    = %d " % status.lamp2
        print "M2       = %d " % status.M2Position
        print "Filter   = %d " % status.FilterPosition
        print ""
        
    except:
        traceback.print_exc()
        status = 1
 
        
if __name__ == "__main__":
    connect()
    print "#######################################"
    sayHello()
    #getStatus()
    #setFilter("Filter5")
    #connectToCamera()
    #setExposureTime(500.0)
    #startCooling()
    #startExposure()
    #time.sleep(3)
    #stopCooling()
    #disConnectToCamera()
    disconnect()
    

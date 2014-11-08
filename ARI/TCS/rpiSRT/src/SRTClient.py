import sys, traceback, Ice
import Demo


class MyCallback(object): 
    def __init__(self):
        pass

    def getNameCB(self):
        print "listo"

    def failureCB(self, ex):
        print "Exception is: " + str(ex)


status = 0
ic = None
try:
    ic = Ice.initialize(sys.argv)
    base = ic.stringToProxy("SimplePrinter:default -h 192.168.0.9 -p 10000")
    printer = Demo.PrinterPrx.checkedCast(base)
    if not printer:
        raise RuntimeError("Invalid proxy")

    #printer.printString("Hello World!")
    cb1 = MyCallback()
    printer.begin_printString("Hola Asincrono", cb1.getNameCB, cb1.failureCB);
    print "llegue primero"

except:
    traceback.print_exc()
    status = 1

if ic:
    # Clean up
    try:
        ic.destroy()
    except:
        traceback.print_exc()
        status = 1

sys.exit(status)

LIBFTDI=libftd2xx.a

all:
	g++ -c CUSBSA.cpp -o CUSBSA.o
	g++ -shared CUSBSA.o -lshapi -lftd2xx -lpthread -ldl -lrt -o libCUSBSA.so
	g++ main.cpp -lCUSBSA -lshapi -lftd2xx -lpthread -ldl -lrt -o testSH
	@echo "Building python wrapper for CUSBSA"
	swig -python -c++ CUSBSA.i
	g++ -c CUSBSA_wrap.cxx -I/usr/include/python2.7
	g++ -shared CUSBSA_wrap.o -L./ -lCUSBSA -lshapi  -lftd2xx -lpthread -o _CUSBSA.so
	@echo "Building python wrapper for SHLAPI"
	swig -python -c++ SHLAPI.i
	g++ -c SHLAPI_wrap.cxx -I/usr/include/python2.7
	g++ -shared SHLAPI_wrap.o -lshapi  -lftd2xx -lpthread -o _SHLAPI.so


clean:
	rm -f *.o
	rm -f *~
	rm -f testSH
	rm -f libCUSBSA.so
	rm -f _CUSBSA.so
	rm -f CUSBSA_wrap.cxx
	rm -f *.pyc
	rm -f CUSBSA.py	
	rm -f SHAPI.py
	rm -f _SHLAPI.so
	rm -f SHLAPI_wrap.cxx

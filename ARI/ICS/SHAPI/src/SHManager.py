import CUSBSA
import sys
import ctypes

class SHManager:
   def __init__(self):
      self.sh = CUSBSA.CUSBSA()
      self.MAXBW = 40e6
      self.MAXFREQ = 4.4e9
      self.bw = 40e6
      self.fc = 1420.4e6
      self.fi = 0.0;
      self.ff = 0.0;
      self.FFT = 64
      self.filename = "default.txt"
      self.amp = []
      self.freq = []
      self.num_channel = 0
      self.update_freq()
   def __del__(self):
      #clean up
      del(self.amp)
      del(self.freq)

   def init_hound(self):
      val = self.sh.Initialize()
      if(val == 100):
          print "Could not communicate with the SH Device, make sure it is connected and try again"
          sys.exit()

      print "Configuring SH ..."
      self.sh.Configure(0.0, 1, 1, 1, 0, 0)
      print "Done. Ready for hutting!"
   def update_freq(self):
      _fi = self.fc - self.bw/2.0
      _ff = self.fc + self.bw/2.0
      print "Update frequencies: existent fi %0.f will be updated to %0.f" % (self.fi, _fi)
      print "Update frequencies: existent ff %0.f will be updated to %0.f" % (self.ff, _ff)
      if( _ff > self.MAXFREQ):
          print "new value of ff %0.f excceeds the maximum allowed value, %0.f will be used instead" % (_ff, self.MAXFREQ)
          _ff = self.MAXFREQ
      self.ff = _ff
      self.fi = _fi

   def set_bw (self, _bw):
      if (_bw > self.MAXBW):
          print "Requested bandwidth %0.f exceeds the maximum allowed value, %0.f will be used instead" % (_bw, self.MAXBW)
          _bw = self.MAXBW
      print "Set bandwidth: existent bw %0.f Hz will be updated to %0.f Hz" % (self.bw, _bw)
      self.bw = _bw 
      self.update_freq()
   def set_fc (self, _fc): 
       print "Set center frequency: existent fc %0.f Hz will be updated to %0.f Hz" % (self.fc, _fc)
       self.fc = _fc
       self.update_freq()
   def set_file_name(self, _filename):
       print "Set file name: existent output file %s will be updated to %s" % (self.filename, _filename)
       self.filename = _filename
   def get_spectrum(self): 
       print "Adquiring single spec ..."
       num_channel = self.sh.SlowSweep(self.fi, self.ff, self.FFT)
       #num_channel = self.sh.FastSweep(310.0e6, 390.0e6)
       
       pA = ctypes.cast( self.sh.dTraceAmpl.__long__(), ctypes.POINTER( ctypes.c_double ) )
       pF = ctypes.cast( self.sh.dTraceFreq.__long__(), ctypes.POINTER( ctypes.c_double ) )
       print "num_channel %d " %(num_channel)

       self.num_channel = num_channel
       self.amp = []
       self.freq = []

       for i in range(0, num_channel):
          print "iteration %d" %i
          print pA[i]
          self.amp.append(pA[i])
          print pF[i]
          self.freq.append(pF[i])
       print "ready."
       
   def write_spectrum(self):
       print "Writting data to %s ..." % self.filename
       f = open(self.filename, 'w')
       for i in range(0, self.num_channel):
           f.write("%0.10f    %0.10f \r\n" % (self.freq[i], self.amp[i]) )
       f.close()
       print "ready."
       
if __name__ == "__main__":
    print "Staring SHManager"
    sh = SHManager()
    sh.init_hound()
    sh.set_bw(41e6)
    sh.set_fc(1421.0e6)
    sh.set_file_name("hola.txt")
    sh.get_spectrum()
    sh.write_spectrum()
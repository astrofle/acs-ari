
from SRTControlClient1 import *

srt = SRT()
srt.setIP('192.168.0.6 -p 10000')
srt.connect()
srt.SetSerialPort('ttyUSB0')
srt.Init('parametersV01')
srt.SetFreq(1420.4,'3')
srt.GetSpectrum()
srt.tracking('Rosett')
srt.StopTrack()
srt.StopSpectrum()
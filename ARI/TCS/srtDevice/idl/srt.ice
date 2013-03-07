#ifndef SRT_ICE
#define SRT_ICE

module OUC 
{

interface SRT
{
    idempotent void sayHello(int delay);
    //idempotent void shutdown();
  
    //EncoderData getEncodersPosition()
    //     throws TelescopeNotConfiguredEx;
    //RawEncoderData getRawEncodersPosition() 
    //     throws TelescopeNotConfiguredEx;	    
    //TelescopeConfigData getConfiguration()
    //	 throws TelescopeNotConfiguredEx;	
    //TelescopeData getPosition()
    //	 throws TelescopeNotConfiguredEx;	
    //bool isConfigured();
    //bool isTracking();

    //void setConfiguration(string fileName)
    //     throws NotConfigurationFileEx;
    //void setTarget(TelescopePosition targetPos)
    //	 throws TelescopeNotConfiguredEx, TargetOutOfLimitsEx;
    //void setOffset(TelescopePosition offsetPos)
    //	 throws TelescopeNotConfiguredEx, TargetOutOfLimitsEx;
    //void setTracking(TrackingInfo trkInfo)
    //     throws TelescopeNotConfiguredEx;
    //void parkTelescope()
    //     throws TelescopeNotConfiguredEx;
    //void parkTelescopeCap()
    //     throws TelescopeNotConfiguredEx;
    //void parkTelescopeAdvance(bool cap)
    //     throws TelescopeNotConfiguredEx;
    //void stopTelescope(TelescopeDirection dir)
    //     throws TelescopeNotConfiguredEx;
    //void moveToTarget()
    //     throws TelescopeNotConfiguredEx;
    //void handsetSlew(SlewInfo slew)
    //     throws TelescopeNotConfiguredEx; 	 
    //int readDeviceMemory(int deviceId, int address, int value);
    //int setDeviceMemory(int deviceId, int address, int value);
};
};
	

#endif

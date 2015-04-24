module SRTControl{
	sequence<string> ports;
	sequence<float> spectrum;
	
	struct AntennaStatus
        {
        float az;
        float el;
        float aznow;
        float elnow;
        int axis;
        int tostow;
        int elatstow;
        int azatstow;
        int slew;
        string serialport;
        string lastSRTCom;
        string lastSerialMsg;
        };

	sequence<AntennaStatus> anst;

	struct specs{
		spectrum spec;
		spectrum avspec;
		spectrum avspecc;
		spectrum specd;
	};
	
	sequence<specs> spectrums;

	interface telescope{
		void message(string s, out string r);
		void SRTGetSerialPorts(out ports u);
		void SRTSetSerialPort(string s, out string r);
		void SRTinit(string s, out string r);
		void SRTStow(out string r);
		void SRTStatus(out AntennaStatus l);
		void SRTAzEl(float az, float el, out string r);
		void SRTThreads(out string r);
		void serverState(out string r);
		void SRTSetFreq(float freq, string receiver, out string r);
		void SRTGetSpectrum(out specs sp);
		void SRTDoCalibration(string method, out float r);
		void SRTGetName(out float r);
	};
};


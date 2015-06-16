module SRTControl{
	sequence<string> ports;
	sequence<float> spectrum;
	
	struct AntennaStatus
        {
        string now;
        string name;
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

	struct stamp
	    {
		string name;
		string timdate;
		float aznow;
		float elnow;
		float temperature;
		float freq0;
		int av;
		int avc;
		int nfreq;
		float freqsep;
		};

	struct specs{
		stamp sampleStamp;
		spectrum spec;
		spectrum avspec;
		spectrum avspecc;
		spectrum specd;
	};
	
	sequence<specs> spectrums;

	struct inuse{
	    bool use;
	    string proc;
	    };

	interface telescope{
		void message(string s, out string r);
		void SRTGetSerialPorts(out ports u);
		void SRTSetSerialPort(string s, out string r);
		void SRTinit(string s, out string r);
		void SRTStow(out string r);
		void SRTStatus(out AntennaStatus l);
		void SRTgetParameters(out string r);
		void SRTAzEl(float az, float el, out string r);
		void SRTStopSlew(out string r);
		void SRTThreads(out string r);
		void serverState(out string r);
		void SRTSetFreq(float freq, string receiver, out string r);
		void SRTGetSpectrum(out specs sp);
		void SRTDoCalibration(string method, out float r);
		void SRTSetazeloff(float azoff, float eloff, out string r);
		void SRTGetName(out string r);
		void SRTClear(out string r);
		void SRTsetMode(string mode, out string r);
		void SRTOnTarget(out string r);
		void SRTportInUse(out inuse p);
	};
};


module SRTClient{
	sequence<float> spectrum;
	
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

    struct state{
        string name;
        string time;
        string SRTState;
		string SRTonTarget; 
		string SRTMode; 
		string SRTTarget; 
		string SRTTrack; 
		string enObs; 
		string newAzEl; 
		string enSRT; 
		string enSpec; 
		string slewing; 
		string cmdstop; 
		string InMoving;  
		string getStatus;  
		string portInUse;  
		string spectra; 
		string RxSwitchMode;  
		string toSource; 
		string SRTinitialized; 
		string initialized; 
		string toStow;  
		string Target;  
		string obsTarget;
		string az;
		string el;
		string aznow;
		string elnow;
		string axis;
		string tostow;
		string elatstow;
		string azatstow;
		string slew;
		string serialport;
		string lastSRTCom;
		string lastSerialMsg;
    };

	sequence<specs> spectrums;

	interface Client{
		void message(string s, out string r);
		void setup(out string r);
		void obsSRT(string mode, string target, out string r);
		void StopObs(out string r);
		void getSpectrum(out specs sp);
		void setFreq(float freq, string rmode, out string r);
		void stopSpectrum(out string r);
		void startSpectrum(out string r);
		void setRxMode(string mode, out string r);
		void SRTstate(out state st);
		void offsetPointing(float azoff, float eloff, out string r);
		void NpointScan(int points, float delta, bool sp, out sequence l);
		void SRTStow(out string r);
	};
};
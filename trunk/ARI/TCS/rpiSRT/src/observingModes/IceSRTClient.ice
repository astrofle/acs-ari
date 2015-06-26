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
        
    struct piu{
        bool InUse;
        string Routine;
        };


    struct state{
        string name;
        string time;
        string SRTState;
		bool SRTonTarget; 
		string SRTMode; 
		string SRTTarget; 
		bool SRTTrack; 
		bool enObs; 
		bool newAzEl; 
		bool enSRT; 
		bool enSpec; 
		bool slewing; 
		bool cmdstop; 
		bool IsMoving;  
		bool getStatus;  
		piu portInUse;  
		bool spectra; 
		string RxSwitchMode;  
		int toSource; 
		bool SRTinitialized; 
		bool initialized;  
		string Target;  
		string obsTarget;
		float az;
		float el;
		float aznow;
		float elnow;
		float azoffset;
		float eloffset;
		int axis;
		bool tostow;
		bool elatstow;
		bool azatstow;
		bool slew;
		string serialport;
		string lastSRTCom;
		string lastSerialMsg;
    };

	sequence<specs> spectrums;

	sequence<float> delta;
	
	struct mapel
	    {
	    delta azeloff;
	    specs maspecs;
	    };

    sequence<mapel> map;

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
		void NpointScan(int points, float delta, bool sp, out map ml);
		void SRTStow(out string r);
		void ClientThreads(out string r);
		void SRTStopGoingToTarget(out string r);
		void ClientShutdown(out string r);
	};
};
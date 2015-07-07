module ARIAPI{

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

	struct astro
	    {
	    string source;
	    float az;
	    float el;
	    };
	
	sequence<astro> sources;
	
		sequence<float> delta;
	
	struct mapel
	    {
	    delta azeloff;
	    specs maspecs;
	    };

    sequence<mapel> map;
    
    
    dictionary<string, specs> lsp;
    
    sequence<string> txtList;
    dictionary<string, string> txtDict;
    dictionary<string, bool> boolDict;
    
    struct RxSet{
        float freq;
        string mode;
        };
    
    sequence<RxSet> RxSetList;
    dictionary<string, RxSetList> RXSetup;
    
    struct OMstate{
		string observingMode;
		txtList nodes;
		txtDict ARIcontrollers;
		bool setupInProgress;
		boolDict initialized;
		boolDict atStow;
		bool stowInProgress;
		string mode;
		txtDict RxSwitchMode;
		RXSetup SRTRxSetup;
		float ArrayFrequency;
		string ArrayRxMode;
		bool getClientStatus;
		bool ArrayMovingToTarget;
		bool ArrayOnTarget;
		bool ArrayStopCommand;
		delta ArrayOffsets;
		bool ScanMapInProgress;
		bool ReadSpectrum;
		boolDict NewSpectrumToRead;
		bool WaitingSpectrum;
    };

    struct piu{
        bool InUse;
        string Routine;
        };

    struct ClState{
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

    dictionary<string, ClState> ClStateDict;


	struct SHstamp{
		string time;
		int seq;
		float freqi;
		float freqf;
		int channels;
		float chbw;
		float spectralPower;
		float centerFreqPower;
		float SRT1aznow;
		float SRT1elnow;
		float SRT2aznow;
		float SRT2elnow;
		float az;
		float el;
	};
	struct SHspectrum{
		SHstamp samplestamp;
		spectrum SHspec;
	};

    dictionary<string, SHspectrum> lspSH;

	interface API{
		void testConn(string s, out string r);
		void setObservingMode(string s1, string s2, out string r);
		void createObservingMode(out string r);
		void setupArray(out string r);
        void observeWithArray(string s1, string s2, out string r);
        void setRxArray(float f1, int i1, out string r);
        void setRxSwMode(string s1, string s2, out string r);
        void enableSpectrumArray(out string r);
        void disableSpectrumArray(out string r);
        void npointScanMap(int points, float delta, bool spec, out map sm);
        void findRaDecSources(out sources r);
        void findPlanets(out sources r);
        void findStars(out sources r);
        void clientShutdown(out string r);
        void obsModeShutdown(out string r);
        void stowArray(out string r);
        void stopArray(out string r);
        void stopGoingToTarget(out string r);
        void setOffsetPointing(float f1, float f2, out string r);
        void getObsModeState(out OMstate r);
        void getArrayState(out ClStateDict r);
        void getLastSpectrum(out lsp sp);
        void setARISH(float fc, float bw, out string r);
        void getLastSHSpectrum(out lspSH sp);
	};
};	


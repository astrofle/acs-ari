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

	sequence<specs> spectrums;

	interface Client{
		void message(string s, out string r);
		void setup(out string r);
		void trackSource(string s, out string r);
		void stopTrack(out string r);
		void getSpectrum(out specs sp);
		void setFreq(float freq, string rmode, out string r);
		void stopSpectrum(out string r);
		void startSpectrum(out string r);
		void setRxMode(string mode, out string r);
	};
};
module SRTClient{
	sequence<float> spectrum;

	struct stamp
	    {
		string name;
		string timdate;
		float aznow;
		float elnow;
		};

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
		
	sequence<specs> spectrums;

	interface Client{
		void message(string s, out string r);
		void setup(out string r);
		void trackSource(string s, out string r);
		void stopTrack(out string r);
		void getSpectrum(out specs sp);
	};
};
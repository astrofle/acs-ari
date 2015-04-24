module SRTClient{
	struct stamp
	    {
		string name;
		string timdate;
		float aznow;
		float elnow;
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
		void trackSource(string s, out specs sp);
		void stopTrack(out string r);
	};
};
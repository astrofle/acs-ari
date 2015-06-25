#include <IceSRTClient.ice>

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
        void getObsModeState(out string r);
        void getArrayState(out string r);
	};
};	


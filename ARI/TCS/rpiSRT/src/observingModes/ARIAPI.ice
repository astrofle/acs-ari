module ARIAPI{

	struct astro
	    {
	    string source;
	    float az;
	    float el;
	    };
	
	sequence<astro> sources;

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
        void npointScanMap(int points, float delta, bool spec, out string r);
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


module SRTClient{
	interface Client{
		void message(string s, out string r);
		void setup(out string r);
		void tracking(string s, out string r);
	};
};
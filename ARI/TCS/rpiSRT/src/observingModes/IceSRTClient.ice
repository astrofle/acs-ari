module SRTClient{
	interface Client{
		void message(string s, out string r);
		void setup(out string r);
		void trackSource(string s, out string r);
	};
};
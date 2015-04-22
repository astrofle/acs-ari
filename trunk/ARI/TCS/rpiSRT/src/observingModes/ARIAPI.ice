module ARIAPI{
	interface API{
		void testConn(string s, out string r);
		void ChooseObservingMode(string s1, string s2, out string r);
		void Connect(out string r);
		void Initialize(out string r);
		void SetTarget(string s1, float s2, int s3, out string r);
		void FindSources(out string r);
		void StartTracking(out string r);
		void StopTracking(out string r);
	};
};


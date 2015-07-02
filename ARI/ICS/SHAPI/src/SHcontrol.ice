module SHControl{
	sequence<float> spectrum;
	sequence<float> power;

	struct SHstamp{
		string time;
		int seq;
		float freqi;
		float freqf;
		int channels;
		float chbw;
	};
	struct SHspectrum{
		SHstamp samplestamp;
		spectrum SHspec;
	};

	interface SignalHound{
		void message(string s, out string r);
		void SHinitHound(out string r);
		void SHupdateFreq(out string r);
		void SHsetBW(float bw, out string r);
		void SHsetFc(float fc, out string r);
		void SHsetFileName(string fn, out string r);
		void SHsetFFT(int fft, out string r);
		void SHgetSpectrum(out SHspectrum sp);
		void SHgetRBW(out string r);
		void SHchwToFFTSize(int chw, out string r);
		void SHgetCHW(out string r);
		void SHsetCHW(int chw, out string r);
		void SHwriteSpectrum(out string r);
		void SHmakeHead(string ant1, string ant2, string source, out string r);
		void SHvalidFFTSize(int fft, out string r);
		void SHgetSpectralPower(out power r);
	};
};





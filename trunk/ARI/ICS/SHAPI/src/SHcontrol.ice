module SHControl{
	interface SignalHound{
		void message(string s, out string r);
		void SHinit_hound(out string r);
		void SHupdate_freq(out string r);
		void SHset_bw(float bw, out string r);
		void SHset_fc(float fc, out string r);
		void SHset_file_name(string fn, out string r);
		void SHset_fft(int fft, out string);
		void SHget_spectrum(out string r);
		void SHget_RBW(out string r);
		void SHchw_to_fftSize(int chw, out string r);
		void SHget_chw(out string r);
		void SHset_chw(int chw, out string r);
		void SHwrite_spectrum(out string r);
		void SHmake_head(string ant1, string ant2, string source, out string r);
		void SHvalid_fft_size(fft);
	};
};





module SRTControl{
	sequence<string> ports;
	struct AntennaStatus
        {
        float az;
        float el;
        float aznow;
        float elnow;
        int axis;
        int tostow;
        int elatstow;
        int azatstow;
        int slew;
        string serialport;
        string lastSRTCom;
        string lastSerialMsg;
        };

	interface telescope{
		void message(string s, out string r);
		void SRTGetSerialPorts(out ports u);
		void SRTSetSerialPort(string s, out string r);
		void SRTinit(string s, out string r);
		void SRTStow(out string r);
		void SRTStatus(out AntennaStatus l);
		void SRTAzEl(float az, float el, out string r); 
	};
};


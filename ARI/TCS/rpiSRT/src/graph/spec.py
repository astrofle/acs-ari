import os
import time

com1 = "scp -Cp -o \"ProxyCommand ssh rolguin@dev01.bluemonster.cl nc localhost 7000\" srt@localhost:CURRENTLY_MOD/rolguin/acs-ari/trunk/ARI/TCS/rpiSRT/src/clients/SRT_client/fspec.csv ."
com2 = "scp -Cp -o \"ProxyCommand ssh rolguin@dev01.bluemonster.cl nc localhost 7000\" srt@localhost:CURRENTLY_MOD/rolguin/acs-ari/trunk/ARI/TCS/rpiSRT/src/clients/SRT_client/fspecd.csv ."
com3 = "scp -Cp -o \"ProxyCommand ssh rolguin@dev01.bluemonster.cl nc localhost 7000\" srt@localhost:CURRENTLY_MOD/rolguin/acs-ari/trunk/ARI/TCS/rpiSRT/src/clients/SRT_client/favspec.csv ."
com4 = "scp -Cp -o \"ProxyCommand ssh rolguin@dev01.bluemonster.cl nc localhost 7000\" srt@localhost:CURRENTLY_MOD/rolguin/acs-ari/trunk/ARI/TCS/rpiSRT/src/clients/SRT_client/favspecc.csv ."

while(True):
	os.system(com1)
	os.system(com2)
	os.system(com3)
	os.system(com4)
	time.sleep(1)
	

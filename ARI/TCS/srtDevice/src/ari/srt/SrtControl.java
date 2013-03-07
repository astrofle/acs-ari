package ari.srt;

import org.zeromq.ZMQ;

import com.google.protobuf.InvalidProtocolBufferException;

import ari.protocol.gen.SrtProtocol;

public class SrtControl {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		System.out.println("Hello SRT device!");
		ZMQ.Context context = ZMQ.context(1);
		ZMQ.Socket socket = context.socket(ZMQ.REP);
		SrtDevice dev = new SrtDevice();
		int mm;
		int count;
		
		
		socket.bind("tcp://*:5556");	
		
		while(true) {
			byte[] rawdata = socket.recv(0);
			String reply = "ack";
			socket.send(reply.getBytes(),0);			
		    
			try {
				SrtProtocol.command cmd = SrtProtocol.command.parseFrom(rawdata);
				System.out.println("cmd id=" + cmd.getCommandId());				
				mm = cmd.getParam(0);
				System.out.println("cmd param=" + mm);
				
				count = cmd.getParam(1);
				System.out.println("cmd param=" + count);
				
				dev.azel2(mm, count);
			} catch(InvalidProtocolBufferException e) {
				e.printStackTrace();
			}
		}
	}

}

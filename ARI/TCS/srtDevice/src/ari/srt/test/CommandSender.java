package ari.srt.test;

import java.util.Arrays;

import org.zeromq.ZMQ;

import ari.protocol.gen.SrtProtocol;

public class CommandSender {

	/**
	 * @param args
	 */
	public static void main(String[] args) throws InterruptedException {
		// TODO Auto-generated method stub
		ZMQ.Context context = ZMQ.context(1);
		ZMQ.Socket socket = context.socket(ZMQ.REQ);
		socket.connect("tcp://localhost:5556");
		int param1 = 0;
		int param2 = 0;
		
		System.out.println("len=" + args.length);
		if (args.length != 3) {
			System.out.println("srt_cmd_sender <cmd> param1 param2");
		} else {
			System.out.println("cmd=" + args[0]);
			
			param1 = Integer.parseInt(args[1]);
			System.out.println("param1=" + param1);
			
			param2 = Integer.parseInt(args[2]);
			System.out.println("param2=" + param2);
			
			
			SrtProtocol.command cmd = SrtProtocol.command.newBuilder().setCommandId(0).addParam(param1).addParam(param2).build();
			byte[] data = cmd.toByteArray();		
			System.out.println("Sending cmd id=" + cmd.getCommandId() + ", " + cmd.getParam(0) + ", " + cmd.getParam(1));
			socket.send(data, 0);			
			byte[] reply = socket.recv(0);
			System.out.println("reply=" + reply);
		}
//		int i=0;
//		while(true) {
//			
//			SrtProtocol.command cmd = SrtProtocol.command.newBuilder().setCommandId(i).addParam(1).addParam(5000).build();
//			byte[] data = cmd.toByteArray();		
//			System.out.println("Sending cmd id=" + cmd.getCommandId() + ", " + cmd.getParam(0) + ", " + cmd.getParam(1));
//			socket.send(data, 0);			
//			byte[] reply = socket.recv(0);
//			
//			Thread.sleep(1000);
//			i++;
//		}
	}

}

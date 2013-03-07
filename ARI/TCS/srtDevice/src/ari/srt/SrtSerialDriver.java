package ari.srt;

import gnu.io.CommPortIdentifier;
import gnu.io.PortInUseException;
import gnu.io.SerialPort;
import gnu.io.UnsupportedCommOperationException;
import java.io.*;
import java.util.*;
import java.util.StringTokenizer;



public class SrtSerialDriver {

	
    CommPortIdentifier portId;
    Enumeration portList;
    InputStream inputStream;
    OutputStream outputStream;
    SerialPort serialPort;
    int MAX_READING_TRIES = 100;
    int MAX_MESSAGE_LENGTH = 80;
    int READING_PAUSE = 100;  //milliseconds
	int messageCount = 0;

	
    public SrtSerialDriver(String portName) {
    	
    	int found = 0;
    	portList = CommPortIdentifier.getPortIdentifiers();

    	while (portList.hasMoreElements()) {
    		portId = (CommPortIdentifier) portList.nextElement();

    		System.out.println("SRT is configured to use port " + portName);
    		System.out.println("Checking system available ports ...\n processing port=" + portId.getName());

    		if (portId.getName().trim().equals(portName)) {
    			
    			try {
    				System.out.println("Found the righ serial port, initializing ...!");
    				serialPort = (SerialPort) portId.open("SRT", 2000);
    				found = 1;
    			} catch(PortInUseException e) {
    				System.out.println(portId.getName());
    				System.out.println(e);
    				System.out.println("Port in use, try again");
    				System.exit(0);
    			}
    			
    			try {
    				outputStream = serialPort.getOutputStream();
    				inputStream = serialPort.getInputStream();
    			} catch(IOException e) {
    				System.out.println(e);
    			}
    			
    			try {
    				/*if (g.get_hh90() == 0 && g.get_sg2100() == 0) {*/
    				serialPort.setSerialPortParams(2400,
    						SerialPort.DATABITS_8,
    						SerialPort.STOPBITS_1,
    						SerialPort.PARITY_NONE);
    				/*
	                    } else {
	                         serialPort.setSerialPortParams(9600,
	                                                        SerialPort.DATABITS_8,
	                                                        SerialPort.STOPBITS_1,
	                                                        SerialPort.PARITY_NONE);
	                    }
    				 */
    			} catch(UnsupportedCommOperationException e) {
    				System.out.println(e);
    			}
    			
    	    	try {
    	    		serialPort.enableReceiveTimeout(100);
    	    	} catch(UnsupportedCommOperationException e) {
    	    		System.out.println(e);
    	    	}
    	    	
    	    	// port found, no need to continue
    	    	break;    	    	
    		} 
    	}

    	if (found == 0) {
    		
    		portList = CommPortIdentifier.getPortIdentifiers();
    		System.out.println("------------------------");
    		System.out.println("port " + portName + " was not found in the system, make sure you have the right permission. Detected ports are:");
    		while (portList.hasMoreElements()) {
    			portId = (CommPortIdentifier) portList.nextElement();
    			System.out.println(portId.getName());
    		}
    		System.exit(0);
    	}   	

    }
    
    public char[] command(byte[] cmd) {
    	
    	int n, rcount;
    	char buffer[] = new char[MAX_MESSAGE_LENGTH];
    	rcount = 0;
    	int c = 0 ;
    	int i = 0;
    	int j = 0;

    	try {   	
    		
    		//String cmd = "  move 2 5000\n";
    		System.out.println("===========================================");
    		System.out.println("sending cmd=");
    		for(byte b: cmd) 
    			System.out.print((char)b + " ");    
    		System.out.println("");
    		
    		outputStream.write(cmd);
    		
    		//wait and read the answer back
    		while(true) {    		

    			c = inputStream.read();    			
    			if(c == -1) {
    				//not ready yet, wait
    				j++; 
    				if(j > MAX_READING_TRIES) {
    					//System.out.println("msg " + "#" + messageCount + " time out, waiting for response: " + MAX_READING_TRIES * READING_PAUSE + " milliseconds");
    					//throw timeout exception
    					throw new IOException("time out!!!");
    				}
    				Thread.sleep(100);
    				
    			} else {
    				//System.out.println("received: " + (char)j);
    				buffer[0] = (char)c;
    				i = 1;
    				//keep reading the rest of the message, try 100 times at most.
    				while(i < MAX_MESSAGE_LENGTH) {
    					//read 1 byte at time
    					c = inputStream.read();
    					if(c>=0) {
            				buffer[i] = (char)c;
            				i++;
            			} else if(c == -1) {
            				//end of message or incomplete message:
        	    			//we suppose all the message will arrive continuously
        	    			//if a -1 is read from the buffer, then end of message
        	    			//and quit the loop
            				break;
            			} else {
            				//unexpected message
            				break;
            			}   					
    					
    	    			//if(i % 10 == 0)
    	    			//	System.out.println("i =" + i);        
    					
    				}   				
    				
    				messageCount ++;
    				
    				if(j > MAX_READING_TRIES) {
    					System.out.println("msg " + "#" + messageCount + " time out, waiting for response: " + MAX_READING_TRIES * READING_PAUSE + " milliseconds");
    					//throw timeout exception
    				}
    				
    				if(i == MAX_MESSAGE_LENGTH) {
    					System.out.println("msg " + "#" + messageCount + " reach max length of the message : " + MAX_MESSAGE_LENGTH);
    				} else {
    					System.out.println("msg " + "#" + messageCount + " Received: ");
    				}    				
    				
    				for (int z=0; z < i;  z++) {
    					System.out.print((int)buffer[z] + " ");
    				}    				
    				System.out.println("");
    				
    				for (int z=0; z < i;  z++) {
    					System.out.print(buffer[z] + " ");
    				}
    				System.out.println("\nEnd of message");    				
                	System.out.println("----------------------------------");		
              	 	break;
    			}         
    		}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return buffer;
    }

    
	public static void main(String[] args) {

		String portName = "/dev/ttyS0";
		SrtSerialDriver driver = new SrtSerialDriver(portName);
		System.out.println("Serial port " + portName + " is ready ...");
		
		
		for (int i=1; i<10000; i++) {
			String cmd = "  move 3 " + i + "\n";
			System.out.println("sending command: " + cmd);
			char[] response = driver.command(cmd.getBytes());
		}
		
		System.exit(0);		
	}

}

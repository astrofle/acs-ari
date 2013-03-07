package ari.srt;



import java.util.*;
import gnu.io.CommPortIdentifier;
import gnu.io.PortInUseException;
import gnu.io.SerialPort;
import gnu.io.UnsupportedCommOperationException;

import java.io.*;

public class SrtDevice
{
    //private Geom geom = new Geom();
	private SrtSerialDriver driver; 
    private Time t = new Time();
    static CommPortIdentifier portId;
    static Enumeration portList;
    InputStream inputStream;
    static OutputStream outputStream;
    SerialPort serialPort;
    private double ylim = 415.0;
    private double ylim0 = 200.0;
    private int azatstow = 0;
    private int elatstow = 0;

    public SrtDevice() {
        driver = new SrtSerialDriver("/dev/ttyS0");
    }
    
    void azel2(int mm, int count) {
    	String str;    	
    	str = "  move " + mm + " " + count + "\n"; /* need space at start and end */    	
    	try {
    		System.out.println("Sending: " + str );		
    		driver.command(str.getBytes());	    		  		
    	} catch(Exception e) {
    		System.out.println(e);
    	}
    }
    
    
    void azel(double az, double el, global g, disp d, Graphics gg, outfile o) {
    	int i,k, kk, n, mm, ax, axis, count, ccount, rcount, fcount, b2count, region1, region2, region3, flip;
    	double azscale, elscale, azz, ell, ellcount, ellnow, lenzero, ra, dec, glat, glon, vel, sec, x, y;
    	int j;
    	char m[] = new char[80]; /* avoid byte array compiler bug */
    	char recv[] = new char[80];
    	String str, str2;
    	StringTokenizer parser;
    	mm = count = 0;
    	lenzero = 0.0;
    	
    	
    
    	az = az % 360;          /* Fold into reasonable range */
	    if (g.get_south() == 0) {
	        az = az + 360.0;    /* put az in range 180 to 540 */
	        if (az > 540.0)
	            az -= 360.0;
	        if (az < 180.0)
	            az += 360.0;
	    }
	    
	    region1 = region2 = region3 = 0;
	    if (az >= g.get_azlim1() && az < g.get_azlim2() && el >= g.get_ellim1()
	    		&& el <= g.get_ellim2())
	    	region1 = 1;
	    if (az > g.get_azlim1() + 180.0 && el > (180.0 - g.get_ellim2()))
	    	region2 = 1;
	    if (az < g.get_azlim2() - 180.0 && el > (180.0 - g.get_ellim2()))
	    	region3 = 1;
	    if (region1 == 0 && region2 == 0 && region3 == 0) {
	    	//d.dtext(16.0, 48.0, gg, Color.red, "cmd out of limits");
	    	//d.set_bc(Color.black, 4);
	    	System.out.println("Cmd out of limits!");
	    	if (g.get_fstatus() == 1 && g.get_track() != 0)
	    		o.stroutfile(g, "* ERROR cmd out of limits");
	    	//stop tracking
	    	g.set_track(0);
	    	try {
                Thread.sleep(100);
            } catch(InterruptedException e) {
            	System.out.println(e);
            }
	    	return;
	    }
	    
	    flip = 0;
	    if (az > g.get_azlim2() && g.get_pushrod() == 0) {
	        az -= 180.0;
	        el = 180.0 - el;
	        flip = 1;
	    }
	    
	    if (az < g.get_azlim1() && g.get_pushrod() == 0 && flip == 0) {
	        az += 180.0;
	        el = 180.0 - el;
	        flip = 1;
	    }
	    
	    azz = az - g.get_azlim1();
	    ell = el - g.get_ellim1();
	    //scale = 52.0 * 27.0 / 120.0;
	    azscale = g.get_azcounts_per_deg();
	    elscale = g.get_elcounts_per_deg();
	    /* mm=1=clockwize incr.az mm=0=ccw mm=2= down when pointed south */
	    g.set_slew(0);
	    if (g.get_pushrod() == 0)
	    	ellcount = ell * elscale;
	    else {
	    	lenzero = g.get_rod1() * g.get_rod1() + g.get_rod2() * g.get_rod2()
            - 2.0 * g.get_rod1() * g.get_rod2()
            * Math.cos((g.get_rod4() - g.get_ellim1()) * Math.PI / 180.0)
            - g.get_rod3() * g.get_rod3();
        
	    	if (lenzero >= 0.0)
	    		lenzero = Math.sqrt(lenzero);
	    	else
	    		lenzero = 0;
        
	    	ellcount = g.get_rod1() * g.get_rod1() + g.get_rod2() * g.get_rod2()
	    			- 2.0 * g.get_rod1() * g.get_rod2()
	    			* Math.cos((g.get_rod4() - el) * Math.PI / 180.0)
	    			- g.get_rod3() * g.get_rod3();
        
	    	if (ellcount >= 0.0)
	    		ellcount = (-Math.sqrt(ellcount) + lenzero) * g.get_rod5();
	    	else
	    		ellcount = 0;
	    	//increase in length drives to horizon
	    	//System.out.println("ellcount "+ellcount);
	    }
	    
	    if (ellcount > g.get_elcount() * 0.5)
	    	axis = 1;           // move in elevation first
	    else
	    	axis = 0;
	    
	    for (ax = 0; ax < 2; ax++) {
	    	//moving in both axes
	    	if (axis == 0) {
	    		//movement in azimuth, check movement direction
	    		if (azz * azscale > g.get_azcount() * 0.5 - 0.5) {
	    			mm = 1;
	    			count = (int) (azz * azscale - g.get_azcount() * 0.5 + 0.5);
	    		}
	    		if (azz * azscale <= g.get_azcount() * 0.5 + 0.5) {
	    			mm = 0;
	    			count = (int) (g.get_azcount() * 0.5 - azz * azscale + 0.5);
	    		}
	    	} else {
	    		//movement in elevation, check direction
	    		if (ellcount > g.get_elcount() * 0.5 - 0.5) {
	    			mm = 3;
	    			count = (int) (ellcount - g.get_elcount() * 0.5 + 0.5);
	    		}
	    		if (ellcount <= g.get_elcount() * 0.5 + 0.5) {
	    			mm = 2;
	    			count = (int) (g.get_elcount() * 0.5 - ellcount + 0.5);
	    		}
	    	}
	    	
	    	
	        ccount = count;
	        if (g.get_stow() == 1 && g.get_azcmd() == g.get_azlim1()
	            && g.get_elcmd() == g.get_ellim1()) {
	        	//drive to stow 
	            count = 5000;
	            
	            if (axis == 0) {
	                mm = 0;
	                if (azatstow == 1)
	                    count = 0;
	            }
	            
	            if (axis == 1) {
	                mm = 2;
	                //complete azimuth motion to stow before completely drop in elevation
	                if (elatstow == 1 || (ccount <= 2.0 * g.get_countperstep()
	                                      && azatstow == 0))
	                    count = 0;
	            }
	            flip = 0;
	        }
        
	        if (count > g.get_countperstep() && ccount > g.get_countperstep())
	        	count = g.get_countperstep();
	        
	        if (count >= g.get_ptoler() && g.get_track() != -1) {
	            
	        	if (count > g.get_ptoler()) {
	                g.set_slew(1);
	                if(g.get_vsrt() != 2)
	                   //d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: slewing   ");
	                	System.out.println("Slewing ...");
	                //d.set_bc(Color.black, 4);
	                //d.set_bc(Color.black, 3);
	            }
	            
//	            x = g.get_xlast(500);
//	            y = g.get_ylast(500);
//	            if (x != g.get_xlast(0) || y != g.get_ylast(0)) {
//	                d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//	                d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//	            }
	        	
	            x = (int) (g.get_azcmd() * 640.0 / 360.0);
	            if (g.get_south() == 0)
	                x -= 320;
	            if (x < 0)
	                x += 640;
	            if (x > 640)
	                x -= 640;
	            y = (int) (ylim - g.get_elcmd() * (ylim - ylim0) / 90);
	            g.set_xlast(x, 500);
	            g.set_ylast(y, 500);
	            //d.lpaint(gg, Color.yellow, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
	            //d.lpaint(gg, Color.yellow, (double) (x), (double) (y - 10), (double) (x), (double) (y + 10));
	            str = "  move " + mm + " " + count + "\n"; /* need space at start and end */
//	            System.out.println("commands sent in azel(): " + str);
//	            n = 0;
//	            if (g.get_azelsim() != 0) {
//	                if (count < 5000)
//	                    str2 = "M " + count + "\n";
//	                else
//	                    str2 = "T " + count + "\n";
//	                str2.getChars(0, str2.length(), recv, 0);
//	                n = str2.length();
//	            }
	            //d.dtext(16.0, 64.0, gg, Color.black, "trans " + str.substring(0, str.length() - 1) + "     ");
	            //d.ppclear(gg, 16.0, 80.0, 180.0);
	            
	            j = 0;
	            kk = -1;
	            if (g.get_azelsim() == 0) {
	                try {
	                    serialPort.enableReceiveTimeout(100);
	                }
	                catch(UnsupportedCommOperationException e) {
	                    System.out.println(e);
	                }
	                try {
	                    outputStream.write(str.getBytes());
	                    j = n = rcount = kk = 0;
	                    while (kk >= 0 && kk < 3000) {
	                        d.ppclear(gg, 16.0, 48.0, 180.0);
	                        if (axis == 0)
	                            d.dtext(16.0, 48.0, gg, Color.black, "waiting on azimuth   " + kk);
	                        else
	                            d.dtext(16.0, 48.0, gg, Color.black, "waiting on elevation " + kk);
	
	                        j = inputStream.read();
	                        kk++;
	                        if (j >= 0 && n < 80) {
	                            recv[n] = (char) j;
	                            n++;
	                        }
	                        if (n > 0 && j == -1)
	                            kk = -1; // end of message
	
	                        t.getTsec(g, d, gg);
	                    }
	                    d.ppclear(gg, 16.0, 48.0, 180.0);
	                }
	                catch(IOException e) {
	                    System.out.println(e);
	                }
	                // no need to close
	            }
	            if (kk != -1 || (recv[0] != 'M' && recv[0] != 'T')) {
	                d.dtext(16.0, 16.0, gg, Color.red, "comerr j=" + j + " n=" + n + " mm=" + count);
	                g.set_comerr(g.get_comerr() + 1);
	                if (g.get_fstatus() == 1)
	                    o.stroutfile(g, "* ERROR comerr");
	                if (g.get_mainten() == 0)
	                    g.set_stow(1);
	                return;
	            }
	
	            if (g.get_azelsim() != 0 && g.get_azelsim() < 10) {
	                d.ppclear(gg, 16.0, 48.0, 180.0);
	                try {
	                    Thread.sleep(100);
	                }
	                catch(InterruptedException e) {
	                    System.out.println(e);
	                }
	            }
	            str = String.copyValueOf(recv, 0, n - 1);
	            d.ppclear(gg, 16.0, 80.0, 180.0);
	            d.dtext(16.0, 80.0, gg, Color.black, "recv " + str);
	            parser = new StringTokenizer(str);
	            try {
	                str2 = parser.nextToken();
	            }
	            catch(NoSuchElementException e) {
	            }
	            rcount = 0;
	            try {
	                str2 = parser.nextToken();
	                rcount = Integer.valueOf(str2).intValue();
	            }
	            catch(NoSuchElementException e) {
	            }
	            b2count = 0;
	            try {
	                str2 = parser.nextToken();
	                b2count = Integer.valueOf(str2).intValue();
	            }
	            catch(NoSuchElementException e) {
	            }
	            if (count < 5000)
	                fcount = count * 2 + b2count; // add extra 1/2 count from motor coast
	            else
	                fcount = 0;
	            if (rcount < count && ((axis == 0 && g.get_azcmd() != g.get_azlim1())
	                                   || (axis == 1 && g.get_elcmd() != g.get_ellim1()))) {
	                d.dtext(16.0, 48.0, gg, Color.red, "lost count goto Stow");
	                d.dtext(440.0, ylim + 40.0, gg, Color.blue, "ERROR:  ");
	                d.dtext(8.0, ylim + 60.0, gg, Color.black, "received " +
	                        rcount + " counts out of " + count + " counts expected");
	                if (mm == 1)
	                    d.dtext(8.0, ylim + 74.0, gg, Color.black, "while going clockwise in azimuth");
	                if (mm == 0)
	                    d.dtext(8.0, ylim + 74.0, gg, Color.black,
	                            "while going counter-clockwise in azimuth");
	                if (mm == 3)
	                    d.dtext(8.0, ylim + 74.0, gg, Color.black, "while going clockwise in elevation");
	                if (mm == 2)
	                    d.dtext(8.0, ylim + 74.0, gg, Color.black,
	                            "while going counter-clockwise in elevation");
	                d.dtext(8.0, ylim + 88.0, gg, Color.black, "motor stalled or limit prematurely reached");
	
	                if (g.get_fstatus() == 1)
	                    o.stroutfile(g, "* ERROR lost count");
	                if (g.get_mainten() == 0) {
	                    if (mm == 2 && recv[0] == 'T') // could hit limit at source set
	                    {
	                        g.set_elcount(0);
	                        g.set_elnow(g.get_ellim1());
	                    }
	                    elatstow = azatstow = 0;
	                    g.set_stow(1);
	                    g.set_azcmd(g.get_azlim1());
	                    g.set_elcmd(g.get_ellim1());
	                }
	                return;
	            }
	            if (mm == 2 && recv[0] == 'T') {
	                elatstow = 1;
	                g.set_elcount(0);
	                g.set_elnow(g.get_ellim1());
	            }
	            if (mm == 0 && recv[0] == 'T') {
	                azatstow = 1;
	                g.set_azcount(0);
	                g.set_aznow(g.get_azlim1());
	            }
	            if (recv[0] == 'T' && g.get_stow() == 0) {
	                d.dtext(16.0, 32.0, gg, Color.black, "timeout from antenna");
	            }
	            if (recv[0] == 'M') {
	                if (axis == 0) {
	                    azatstow = 0;
	                    if (mm == 1)
	                        g.set_azcount(g.get_azcount() + fcount);
	                    else
	                        g.set_azcount(g.get_azcount() - fcount);
	                }
	                if (axis == 1) {
	                    elatstow = 0;
	                    if (mm == 3)
	                        g.set_elcount(g.get_elcount() + fcount);
	                    else
	                        g.set_elcount(g.get_elcount() - fcount);
	                }
	            }
	            if (g.get_azelsim() == 0) {
	                try {
	                    Thread.sleep(5);
	                }
	                catch(InterruptedException e) {
	                    System.out.println(e);
	                }
	            }
	        }
        
	        axis++;
	        if (axis > 1)
	            axis = 0;
	    }
    
	    if (g.get_track() != -1) {
	        if (g.get_slew() == 1)
	            g.set_track(0);
	        else
	            g.set_track(1);
	    }
	    
		g.set_aznow(g.get_azlim1() - g.get_azcor() + g.get_azcount() * 0.5 / azscale);
	    
		if (g.get_aznow() > 360.0)
	        g.set_aznow(g.get_aznow() - 360.0);
	    
	    if (g.get_pushrod() == 0)
	        ellnow = g.get_elcount() * 0.5 / elscale;
	    else {
	        ellnow = -g.get_elcount() * 0.5 / g.get_rod5() + lenzero;
	        ellnow = g.get_rod1() * g.get_rod1() + g.get_rod2() * g.get_rod2()
	            - g.get_rod3() * g.get_rod3() - ellnow * ellnow;
	        ellnow = ellnow / (2.0 * g.get_rod1() * g.get_rod2());
	        ellnow = -Math.acos(ellnow) * 180.0 / Math.PI + g.get_rod4()
	            - g.get_ellim1();
	        //System.out.println("ellnow "+ellnow);
	    }
	    
	    g.set_elnow(g.get_ellim1() - g.get_elcor() + ellnow);
	    if (g.get_elnow() > 90.0) {
	        if (g.get_aznow() >= 180.0)
	            g.set_aznow(g.get_aznow() - 180.0);
	        else
	            g.set_aznow(g.get_aznow() + 180.0);
	        g.set_elnow(180.0 - g.get_elnow());
	    }
	    if(g.get_vsrt() != 2)
	       d.dtext(670.0, 40.0, gg, Color.black,
	            "azel  " + d.dc(g.get_aznow(), 5, 1) + " " + d.dc(g.get_elnow(), 5, 1) + " deg");
	    x = g.get_xlast(0);
	    y = g.get_ylast(0);
	    d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
	    d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
	    x = (int) (g.get_aznow() * 640.0 / 360.0);
	    if (g.get_south() == 0) {
	        x -= 320;
	        if (x < 0)
	            x += 640;
	    }
	    y = (int) (ylim - g.get_elnow() * (ylim - ylim0) / 90);
	    g.set_xlast(x, 0);
	    g.set_ylast(y, 0);
	    if(g.get_vsrt() != 2) {
	       d.lpaint(gg, Color.red, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
	       d.lpaint(gg, Color.red, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
	    }
	    if (Math.abs(g.get_aznow() - g.get_azlim1()) < 0.1 && Math.abs(g.get_elnow() - g.get_ellim1()) < 0.1) {
	        d.set_bc(Color.green, 3);
	        if(g.get_vsrt() != 2)
	           d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: at stow");
	        g.set_stow(-1);     // at stow
	
	    } else {
	        d.set_bc(Color.black, 3);
	        if (g.get_stow() == -1)
	            g.set_stow(0);
	    }
	    if (g.get_stow() != 0) {
	        g.set_track(0);
	    }
	    sec = (double) t.getTsec(g, d, gg);
	    ra = geom.get_galactic_ra(sec, g.get_aznow(), g.get_elnow(), g, t);
	    dec = geom.get_galactic_dec();
	    glat = geom.get_galactic_glat();
	    glon = geom.get_galactic_glon();
	    vel = geom.get_galactic_vel();
	    if (Math.abs(g.get_fcenter() - 1665.4) < 1.0)
	        g.set_restfreq(1665.4);
	    else
	        g.set_restfreq(1420.406);
	    if (Math.abs(g.get_fcenter() - 1612.231) < 1.0)
	        g.set_restfreq(1612.231);
	    g.set_vlsr(vel);
	    g.set_glat(glat);
	    g.set_glon(glon);
	    if (Math.abs(g.get_fcenter() - 1667.359) < 1.0)
	        g.set_restfreq(1667.359);
	    if(g.get_vsrt() == 2) return;
	    d.dtext(670.0, 120.0, gg, Color.black,
	            "radec " + d.dc(ra, 5, 1) + " hrs " + d.dc(dec, 5, 1) + " deg");
	    d.dtext(670.0, 104.0, gg, Color.black, "Galactic l =" + d.dc(glon, 4, 0) + " b =" + d.dc(glat, 3, 0));
	    d.dtext(665.0, 426.0, gg, Color.black, "VLSR    " + d.dc(vel, 6, 1) + " km/s");
	    vel = -vel - (g.get_fcenter() - g.get_restfreq()) * 299790.0 / g.get_restfreq();
	    d.dtext(665.0, 442.0, gg, Color.black, "Vcenter " + d.dc(vel, 6, 1) + " km/s");
	    d.lpaint(gg, Color.black, 0.0, 85.0, 217.0, 85.0);
	    d.stext(16.0, ylim + 22.0, gg, Color.black,
	            g.get_statnam() + " lat " + d.dc(g.get_lat() * 180.0 / Math.PI, 4, 1) +
	            " lonw " + d.dc(g.get_lon() * 180.0 / Math.PI, 4, 1));
	    d.lpaint(gg, Color.black, 0.0, 0.0, 217.0, 0.0);
	    return;
    }
    

    // command antenna movement
//    void azel(double az, double el, global g, disp d, Graphics gg, outfile o) {
//        int i, k, kk, n, mm, ax, axis, count, ccount, rcount, fcount, b2count, region1, region2, region3, flip;
//        double azscale, elscale, azz, ell, ellcount, ellnow, lenzero, ra, dec, glat, glon, vel, sec, x, y;
//        int j;
//        char m[] = new char[80]; /* avoid byte array compiler bug */
//        char recv[] = new char[80];
//        String str, str2;
//        StringTokenizer parser;
//        mm = count = 0;
//        lenzero = 0.0;
//        if(g.get_vsrt() != 2)
//           d.dtext(670.0, 24.0, gg, Color.black, "cmd " + d.dc(az, 5, 1) + " " + d.dc(el, 5, 1) + " deg");
//        if (g.get_azelsim() == 0) {
//            str = "antenna drive status:";
//            if (g.get_comerr() > 0)
//                str += " comerr= " + g.get_comerr();
//        } else
//            str = "antenna drive simulated";
//        if (g.get_vsrt() == 0)
//            d.dtext(16.0, 32.0, gg, Color.black, str);
//        az = az % 360;          /* Fold into reasonable range */
//        if (g.get_south() == 0) {
//            az = az + 360.0;    /* put az in range 180 to 540 */
//            if (az > 540.0)
//                az -= 360.0;
//            if (az < 180.0)
//                az += 360.0;
//        }
//        region1 = region2 = region3 = 0;
//        if (az >= g.get_azlim1() && az < g.get_azlim2() && el >= g.get_ellim1()
//            && el <= g.get_ellim2())
//            region1 = 1;
//        if (az > g.get_azlim1() + 180.0 && el > (180.0 - g.get_ellim2()))
//            region2 = 1;
//        if (az < g.get_azlim2() - 180.0 && el > (180.0 - g.get_ellim2()))
//            region3 = 1;
//        if (region1 == 0 && region2 == 0 && region3 == 0) {
//            d.dtext(16.0, 48.0, gg, Color.red, "cmd out of limits");
//            d.set_bc(Color.black, 4);
//            if (g.get_fstatus() == 1 && g.get_track() != 0)
//                o.stroutfile(g, "* ERROR cmd out of limits");
//            g.set_track(0);
//            try {
//                    Thread.sleep(100);
//                }
//                catch(InterruptedException e) {
//                    System.out.println(e);
//                    }
//            return;
//        }
//        flip = 0;
//        if (az > g.get_azlim2() && g.get_pushrod() == 0) {
//            az -= 180.0;
//            el = 180.0 - el;
//            flip = 1;
//        }
//        if (az < g.get_azlim1() && g.get_pushrod() == 0 && flip == 0) {
//            az += 180.0;
//            el = 180.0 - el;
//            flip = 1;
//        }
//        azz = az - g.get_azlim1();
//        ell = el - g.get_ellim1();
////    scale = 52.0 * 27.0 / 120.0;
//        azscale = g.get_azcounts_per_deg();
//        elscale = g.get_elcounts_per_deg();
///* mm=1=clockwize incr.az mm=0=ccw mm=2= down when pointed south */
//        g.set_slew(0);
//        if (g.get_pushrod() == 0)
//            ellcount = ell * elscale;
//        else {
//            lenzero = g.get_rod1() * g.get_rod1() + g.get_rod2() * g.get_rod2()
//                - 2.0 * g.get_rod1() * g.get_rod2()
//                * Math.cos((g.get_rod4() - g.get_ellim1()) * Math.PI / 180.0)
//                - g.get_rod3() * g.get_rod3();
//            if (lenzero >= 0.0)
//                lenzero = Math.sqrt(lenzero);
//            else
//                lenzero = 0;
//            ellcount = g.get_rod1() * g.get_rod1() + g.get_rod2() * g.get_rod2()
//                - 2.0 * g.get_rod1() * g.get_rod2()
//                * Math.cos((g.get_rod4() - el) * Math.PI / 180.0)
//                - g.get_rod3() * g.get_rod3();
//            if (ellcount >= 0.0)
//                ellcount = (-Math.sqrt(ellcount) + lenzero) * g.get_rod5();
//            else
//                ellcount = 0;
//// increase in length drives to horizon
////         System.out.println("ellcount "+ellcount);
//        }
//        if (ellcount > g.get_elcount() * 0.5)
//            axis = 1;           // move in elevation first
//
//        else
//            axis = 0;
//        for (ax = 0; ax < 2; ax++) {
//            if (axis == 0) {
//                if (azz * azscale > g.get_azcount() * 0.5 - 0.5) {
//                    mm = 1;
//                    count = (int) (azz * azscale - g.get_azcount() * 0.5 + 0.5);
//                }
//                if (azz * azscale <= g.get_azcount() * 0.5 + 0.5) {
//                    mm = 0;
//                    count = (int) (g.get_azcount() * 0.5 - azz * azscale + 0.5);
//                }
//            } else {
//                if (ellcount > g.get_elcount() * 0.5 - 0.5) {
//                    mm = 3;
//                    count = (int) (ellcount - g.get_elcount() * 0.5 + 0.5);
//                }
//                if (ellcount <= g.get_elcount() * 0.5 + 0.5) {
//                    mm = 2;
//                    count = (int) (g.get_elcount() * 0.5 - ellcount + 0.5);
//                }
//            }
//            ccount = count;
//            if (g.get_stow() == 1 && g.get_azcmd() == g.get_azlim1()
//                && g.get_elcmd() == g.get_ellim1()) // drive to stow
//
//            {
//                count = 5000;
//                if (axis == 0) {
//                    mm = 0;
//                    if (azatstow == 1)
//                        count = 0;
//                }
//                if (axis == 1) {
//                    mm = 2;
//// complete azimuth motion to stow before completely drop in elevation
//                    if (elatstow == 1 || (ccount <= 2.0 * g.get_countperstep()
//                                          && azatstow == 0))
//                        count = 0;
//                }
//                flip = 0;
//            }
//            if (count > g.get_countperstep() && ccount > g.get_countperstep())
//                count = g.get_countperstep();
//            if (count >= g.get_ptoler() && g.get_track() != -1) {
//                if (count > g.get_ptoler()) {
//                    g.set_slew(1);
//                    if(g.get_vsrt() != 2)
//                       d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: slewing   ");
//                    d.set_bc(Color.black, 4);
//                    d.set_bc(Color.black, 3);
//                }
//                x = g.get_xlast(500);
//                y = g.get_ylast(500);
//                if (x != g.get_xlast(0) || y != g.get_ylast(0)) {
//                    d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//                    d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//                }
//                x = (int) (g.get_azcmd() * 640.0 / 360.0);
//                if (g.get_south() == 0)
//                    x -= 320;
//                if (x < 0)
//                    x += 640;
//                if (x > 640)
//                    x -= 640;
//                y = (int) (ylim - g.get_elcmd() * (ylim - ylim0) / 90);
//                g.set_xlast(x, 500);
//                g.set_ylast(y, 500);
//                d.lpaint(gg, Color.yellow, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//                d.lpaint(gg, Color.yellow, (double) (x), (double) (y - 10), (double) (x), (double) (y + 10));
//                str = "  move " + mm + " " + count + "\n"; /* need space at start and end */
//                System.out.println("commands sent in serial port: " + str);
//                n = 0;
//                if (g.get_azelsim() != 0) {
//                    if (count < 5000)
//                        str2 = "M " + count + "\n";
//                    else
//                        str2 = "T " + count + "\n";
//                    str2.getChars(0, str2.length(), recv, 0);
//                    n = str2.length();
//                }
//                d.dtext(16.0, 64.0, gg, Color.black, "trans " + str.substring(0, str.length() - 1) + "     ");
//                d.ppclear(gg, 16.0, 80.0, 180.0);
//                j = 0;
//                kk = -1;
//                if (g.get_azelsim() == 0) {
//                    try {
//                        serialPort.enableReceiveTimeout(100);
//                    }
//                    catch(UnsupportedCommOperationException e) {
//                        System.out.println(e);
//                    }
//                    try {
//                        outputStream.write(str.getBytes());
//                        j = n = rcount = kk = 0;
//                        while (kk >= 0 && kk < 3000) {
//                            d.ppclear(gg, 16.0, 48.0, 180.0);
//                            if (axis == 0)
//                                d.dtext(16.0, 48.0, gg, Color.black, "waiting on azimuth   " + kk);
//                            else
//                                d.dtext(16.0, 48.0, gg, Color.black, "waiting on elevation " + kk);
//
//                            j = inputStream.read();
//                            kk++;
//                            if (j >= 0 && n < 80) {
//                                recv[n] = (char) j;
//                                n++;
//                            }
//                            if (n > 0 && j == -1)
//                                kk = -1; // end of message
//
//                            t.getTsec(g, d, gg);
//                        }
//                        d.ppclear(gg, 16.0, 48.0, 180.0);
//                    }
//                    catch(IOException e) {
//                        System.out.println(e);
//                    }
//                    // no need to close
//                }
//                if (kk != -1 || (recv[0] != 'M' && recv[0] != 'T')) {
//                    d.dtext(16.0, 16.0, gg, Color.red, "comerr j=" + j + " n=" + n + "mm" + count);
//                    g.set_comerr(g.get_comerr() + 1);
//                    if (g.get_fstatus() == 1)
//                        o.stroutfile(g, "* ERROR comerr");
//                    if (g.get_mainten() == 0)
//                        g.set_stow(1);
//                    return;
//                }
//
//                if (g.get_azelsim() != 0 && g.get_azelsim() < 10) {
//                    d.ppclear(gg, 16.0, 48.0, 180.0);
//                    try {
//                        Thread.sleep(100);
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//                str = String.copyValueOf(recv, 0, n - 1);
//                d.ppclear(gg, 16.0, 80.0, 180.0);
//                d.dtext(16.0, 80.0, gg, Color.black, "recv " + str);
//                parser = new StringTokenizer(str);
//                try {
//                    str2 = parser.nextToken();
//                }
//                catch(NoSuchElementException e) {
//                }
//                rcount = 0;
//                try {
//                    str2 = parser.nextToken();
//                    rcount = Integer.valueOf(str2).intValue();
//                }
//                catch(NoSuchElementException e) {
//                }
//                b2count = 0;
//                try {
//                    str2 = parser.nextToken();
//                    b2count = Integer.valueOf(str2).intValue();
//                }
//                catch(NoSuchElementException e) {
//                }
//                if (count < 5000)
//                    fcount = count * 2 + b2count; // add extra 1/2 count from motor coast
//                else
//                    fcount = 0;
//                if (rcount < count && ((axis == 0 && g.get_azcmd() != g.get_azlim1())
//                                       || (axis == 1 && g.get_elcmd() != g.get_ellim1()))) {
//                    d.dtext(16.0, 48.0, gg, Color.red, "lost count goto Stow");
//                    d.dtext(440.0, ylim + 40.0, gg, Color.blue, "ERROR:  ");
//                    d.dtext(8.0, ylim + 60.0, gg, Color.black, "received " +
//                            rcount + " counts out of " + count + " counts expected");
//                    if (mm == 1)
//                        d.dtext(8.0, ylim + 74.0, gg, Color.black, "while going clockwise in azimuth");
//                    if (mm == 0)
//                        d.dtext(8.0, ylim + 74.0, gg, Color.black,
//                                "while going counter-clockwise in azimuth");
//                    if (mm == 3)
//                        d.dtext(8.0, ylim + 74.0, gg, Color.black, "while going clockwise in elevation");
//                    if (mm == 2)
//                        d.dtext(8.0, ylim + 74.0, gg, Color.black,
//                                "while going counter-clockwise in elevation");
//                    d.dtext(8.0, ylim + 88.0, gg, Color.black, "motor stalled or limit prematurely reached");
//
//                    if (g.get_fstatus() == 1)
//                        o.stroutfile(g, "* ERROR lost count");
//                    if (g.get_mainten() == 0) {
//                        if (mm == 2 && recv[0] == 'T') // could hit limit at source set
//                        {
//                            g.set_elcount(0);
//                            g.set_elnow(g.get_ellim1());
//                        }
//                        elatstow = azatstow = 0;
//                        g.set_stow(1);
//                        g.set_azcmd(g.get_azlim1());
//                        g.set_elcmd(g.get_ellim1());
//                    }
//                    return;
//                }
//                if (mm == 2 && recv[0] == 'T') {
//                    elatstow = 1;
//                    g.set_elcount(0);
//                    g.set_elnow(g.get_ellim1());
//                }
//                if (mm == 0 && recv[0] == 'T') {
//                    azatstow = 1;
//                    g.set_azcount(0);
//                    g.set_aznow(g.get_azlim1());
//                }
//                if (recv[0] == 'T' && g.get_stow() == 0) {
//                    d.dtext(16.0, 32.0, gg, Color.black, "timeout from antenna");
//                }
//                if (recv[0] == 'M') {
//                    if (axis == 0) {
//                        azatstow = 0;
//                        if (mm == 1)
//                            g.set_azcount(g.get_azcount() + fcount);
//                        else
//                            g.set_azcount(g.get_azcount() - fcount);
//                    }
//                    if (axis == 1) {
//                        elatstow = 0;
//                        if (mm == 3)
//                            g.set_elcount(g.get_elcount() + fcount);
//                        else
//                            g.set_elcount(g.get_elcount() - fcount);
//                    }
//                }
//                if (g.get_azelsim() == 0) {
//                    try {
//                        Thread.sleep(5);
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//            }
//            axis++;
//            if (axis > 1)
//                axis = 0;
//        }
//        if (g.get_track() != -1) {
//            if (g.get_slew() == 1)
//                g.set_track(0);
//            else
//                g.set_track(1);
//        }
//        g.set_aznow(g.get_azlim1() - g.get_azcor() + g.get_azcount() * 0.5 / azscale);
//        if (g.get_aznow() > 360.0)
//            g.set_aznow(g.get_aznow() - 360.0);
//        if (g.get_pushrod() == 0)
//            ellnow = g.get_elcount() * 0.5 / elscale;
//        else {
//            ellnow = -g.get_elcount() * 0.5 / g.get_rod5() + lenzero;
//            ellnow = g.get_rod1() * g.get_rod1() + g.get_rod2() * g.get_rod2()
//                - g.get_rod3() * g.get_rod3() - ellnow * ellnow;
//            ellnow = ellnow / (2.0 * g.get_rod1() * g.get_rod2());
//            ellnow = -Math.acos(ellnow) * 180.0 / Math.PI + g.get_rod4()
//                - g.get_ellim1();
////        System.out.println("ellnow "+ellnow);
//        }
//        g.set_elnow(g.get_ellim1() - g.get_elcor() + ellnow);
//        if (g.get_elnow() > 90.0) {
//            if (g.get_aznow() >= 180.0)
//                g.set_aznow(g.get_aznow() - 180.0);
//            else
//                g.set_aznow(g.get_aznow() + 180.0);
//            g.set_elnow(180.0 - g.get_elnow());
//        }
//        if(g.get_vsrt() != 2)
//           d.dtext(670.0, 40.0, gg, Color.black,
//                "azel  " + d.dc(g.get_aznow(), 5, 1) + " " + d.dc(g.get_elnow(), 5, 1) + " deg");
//        x = g.get_xlast(0);
//        y = g.get_ylast(0);
//        d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//        d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//        x = (int) (g.get_aznow() * 640.0 / 360.0);
//        if (g.get_south() == 0) {
//            x -= 320;
//            if (x < 0)
//                x += 640;
//        }
//        y = (int) (ylim - g.get_elnow() * (ylim - ylim0) / 90);
//        g.set_xlast(x, 0);
//        g.set_ylast(y, 0);
//        if(g.get_vsrt() != 2) {
//           d.lpaint(gg, Color.red, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//           d.lpaint(gg, Color.red, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//        }
//        if (Math.abs(g.get_aznow() - g.get_azlim1()) < 0.1 && Math.abs(g.get_elnow() - g.get_ellim1()) < 0.1) {
//            d.set_bc(Color.green, 3);
//            if(g.get_vsrt() != 2)
//               d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: at stow");
//            g.set_stow(-1);     // at stow
//
//        } else {
//            d.set_bc(Color.black, 3);
//            if (g.get_stow() == -1)
//                g.set_stow(0);
//        }
//        if (g.get_stow() != 0) {
//            g.set_track(0);
//        }
//        sec = (double) t.getTsec(g, d, gg);
//        ra = geom.get_galactic_ra(sec, g.get_aznow(), g.get_elnow(), g, t);
//        dec = geom.get_galactic_dec();
//        glat = geom.get_galactic_glat();
//        glon = geom.get_galactic_glon();
//        vel = geom.get_galactic_vel();
//        if (Math.abs(g.get_fcenter() - 1665.4) < 1.0)
//            g.set_restfreq(1665.4);
//        else
//            g.set_restfreq(1420.406);
//        if (Math.abs(g.get_fcenter() - 1612.231) < 1.0)
//            g.set_restfreq(1612.231);
//        g.set_vlsr(vel);
//        g.set_glat(glat);
//        g.set_glon(glon);
//        if (Math.abs(g.get_fcenter() - 1667.359) < 1.0)
//            g.set_restfreq(1667.359);
//        if(g.get_vsrt() == 2) return;
//        d.dtext(670.0, 120.0, gg, Color.black,
//                "radec " + d.dc(ra, 5, 1) + " hrs " + d.dc(dec, 5, 1) + " deg");
//        d.dtext(670.0, 104.0, gg, Color.black, "Galactic l =" + d.dc(glon, 4, 0) + " b =" + d.dc(glat, 3, 0));
//        d.dtext(665.0, 426.0, gg, Color.black, "VLSR    " + d.dc(vel, 6, 1) + " km/s");
//        vel = -vel - (g.get_fcenter() - g.get_restfreq()) * 299790.0 / g.get_restfreq();
//        d.dtext(665.0, 442.0, gg, Color.black, "Vcenter " + d.dc(vel, 6, 1) + " km/s");
//        d.lpaint(gg, Color.black, 0.0, 85.0, 217.0, 85.0);
//        d.stext(16.0, ylim + 22.0, gg, Color.black,
//                g.get_statnam() + " lat " + d.dc(g.get_lat() * 180.0 / Math.PI, 4, 1) +
//                " lonw " + d.dc(g.get_lon() * 180.0 / Math.PI, 4, 1));
//        d.lpaint(gg, Color.black, 0.0, 0.0, 217.0, 0.0);
//        return;
//    }
//    
    
    
    
    
    
    
//    double radiodg(double freq, global g, disp d, Graphics gg, outfile o)
//        // communicate with the radiometer
//    {
//        double power, avpower, tsig, a;
//        int k, n, j, mode, i;
//        byte m[] = new byte[10];
//        int recv[] = new int[128];
//        byte b8, b9, b10, b11;
//        power = tsig = 0.0;
//        j = (int) (freq * (1.0 / 0.04) + 0.5); /* bits for reference divider of syn */
//        mode = g.get_digital() - 1;
//        if (g.get_digital() == 4 || g.get_digital() == 5)
//            mode = 0;
//        b8 = (byte) mode;       /* mode */
//        b9 = (byte) (j & 0x3f);
//        b10 = (byte) ((j >> 6) & 0xff);
//        b11 = (byte) ((j >> 14) & 0xff);
//        m[0] = 0;
//        m[1] = (byte) 'f';
//        m[2] = (byte) 'r';
//        m[3] = (byte) 'e';
//        m[4] = (byte) 'q';
//        m[5] = b11;
//        m[6] = b10;
//        m[7] = b9;
//        m[8] = b8;
//        g.set_freqa(((b11 * 256.0 + (b10 & 0xff)) * 64.0 + (b9 & 0xff)) * 0.04 - 0.8);
//        j = n = 0;
//        if (g.get_radiosim() == 0) {
//            try {
//                for (i = 0; i < 9; i++) {
//                    outputStream.write(m[i]);
//                }
//                try {
//                    serialPort.enableReceiveTimeout(100);
//                }
//                catch(UnsupportedCommOperationException e) {
//                    System.out.println(e);
//                }
//                j = n = i = 0;
//                while (i >= 0 && i < 200) {
//                    j = inputStream.read();
//                    if (j >= 0) {
//                        if (n < 128)
//                            recv[n] = j;
//                        n++;
//                    }
//                    i++;
//                    if (n >= 128 && j == -1)
//                        i = -1; // end of message
//
//                }
//                t.getTsec(g, d, gg);
//                d.ppclear(gg, 16.0, 48.0, 180.0);
//                if (i >= 200)
//                    d.dtext(16.0, 48.0, gg, Color.red, "waiting on recvr");
//            }
//            catch(IOException e) {
//                System.out.println(e);
//            }
//        }
//// no need to inputStream.close();
//
//        if (n != 128 && g.get_radiosim() == 0) {
//            d.dtext(16.0, 16.0, gg, Color.red, " error comm with radio " + n);
//            g.set_comerad(g.get_comerad() + 1);
//            if (g.get_fstatus() == 1)
//                o.stroutfile(g, "* ERROR communicating with radio");
//            return -1.0;
//        } else {
//            a = avpower = 0;
//            for (i = 0; i < 64; i++) {
//                if (g.get_radiosim() != 0) {
//                    power = 200.0 + g.get_tspill();
//                    if (g.get_sourn() > 0 && i == 0) {
//                        if (g.get_sounam(g.get_sourn()).lastIndexOf("Moon") > -1)
//                            tsig = 1.0;
//                        if (g.get_sounam(g.get_sourn()).lastIndexOf("Cass") > -1)
//                            tsig = 2.6;
//                        if (g.get_sounam(g.get_sourn()).lastIndexOf("Sun") > -1)
//                            tsig = 1000.0;
//                    }
//                    if (g.get_scan() != 0 || g.get_track() != 0) {
//                        a = g.get_azoff() * Math.cos(g.get_elcmd() * Math.PI / 180.0);
//                        a = (g.get_eloff() * g.get_eloff() + a * a) * 4.0 * 0.7;
//                        a = a / (g.get_beamw() * g.get_beamw());
//                        power += tsig * Math.pow(2.718, -a);
//                    }
//                    try {
//                        Thread.sleep(5);
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                    if (g.get_calon() == 1)
//                        power = power + g.get_tload() - g.get_tspill();
//                    if (g.get_calon() == 2)
//                        power = power + g.get_noisecal();
//                    power += power * gauss() / Math.sqrt(g.get_freqsep() * 1e06 * g.get_intg());
//                    d.dtext(16.0, 80.0, gg, Color.black, "generating random data");
//                    power = power * g.get_graycorr(i);
//                }
//                if (g.get_radiosim() == 0) {
//                    if (i <= 31)
//                        k = (i + 32) * 2;
//                    else
//                        k = (i - 32) * 2;
//                    power = (recv[k] * 256.0 + recv[k + 1]);
//                }
//                if (g.get_digital() < 5)
//                    a = (i - 32) * g.get_freqsep() * 0.4;
//                else
//                    a = 0;
//                if (g.get_graycorr(i) > 0.8)
//                    power = power / (g.get_graycorr(i) * (1.0 + a * a * g.get_curvcorr()));
//                a = g.get_calcons() * power;
//                if (i > 0)
//                    g.set_specd(a, 64 - i); // reverse lower sideband - makes 31 DC
//
//                else
//                    g.set_specd(a, 0);
//                if (i >= 10 && i < 54)
//                    avpower += power;
//            }
//            avpower = avpower / 44.0;
//            a = g.get_calcons() * avpower;
//            d.dtext(8.0, ylim + 40.0, gg, Color.black, "digital Recvr freq: " +
//                    d.dc(g.get_freqa(), 7, 2) + " pwr: "
//                    + d.dc(avpower, 4, 0) + " counts" + " temp: " + d.dc(a, 4, 0) + "K");
//            return a;
//        }
//    }
//
//    double gauss() {
//        double v1, v2, r, fac, amp, vv1;
//        r = v1 = 0.0;
//        while (r > 1.0 || r == 0.0) {
//            v1 = 2.0 * Math.random() - 1.0;
//            v2 = 2.0 * Math.random() - 1.0;
//            r = v1 * v1 + v2 * v2;
//        }
//        fac = Math.sqrt(-2.0 * Math.log(r) / r);
//        vv1 = v1 * fac;
//        amp = vv1;
//        return amp;
//    }
//
//    void cal(int mode, global g, disp d, Graphics gg, outfile o)
//        // command calibration vane
//    {
//
//// mode=0 calout mode=1 calin
//        int j, k, kk, n, i;
//        String str, str2;
//        char m[] = new char[80];
//        char recv[] = new char[80];
//        if (g.get_azelsim() == 0)
//            d.dtext(16.0, 32.0, gg, Color.black, "vane calibrator status:");
//        else
//            d.dtext(16.0, 32.0, gg, Color.black, "calibrator simulated");
//        str = "  move " + (mode + 4) + " 0 \n"; // need space at start and end
//
//        d.dtext(16.0, 64.0, gg, Color.black, "trans " + str.substring(0, str.length() - 1) + "     ");
//        d.ppclear(gg, 16.0, 80.0, 180.0);
//        if (g.get_azelsim() != 0) {
//            str2 = "T \n";
//            str2.getChars(0, str2.length(), recv, 0);
//            n = str2.length();
//        }
//        j = n = kk = 0;
//
//        if (g.get_azelsim() == 0) {
//            try {
//                outputStream.write(str.getBytes());
//                try {
//                    serialPort.enableReceiveTimeout(1000);
//                }
//                catch(UnsupportedCommOperationException e) {
//                    System.out.println(e);
//                }
//                j = n = kk = 0;
//                while (kk >= 0 && kk < 60) {
//                    if (mode == 1)
//                        d.dtext(16.0, 48.0, gg, Color.black, "waiting on calin     " + kk);
//                    else
//                        d.dtext(16.0, 48.0, gg, Color.black, "waiting on calout    " + kk);
//
//                    j = inputStream.read();
//                    kk++;
//                    if (j >= 0 && n < 80) {
//                        recv[n] = (char) j;
//                        n++;
//                    }
//                    if ((n > 0 && j == -1) || j == 13)
//                        kk = -1;
//
//                    t.getTsec(g, d, gg);
//                }
//                d.ppclear(gg, 16.0, 48.0, 180.0);
//            }
//            catch(IOException e) {
//                System.out.println(e);
//            }
//        }
//
//        recv[n] = 0;
//        if (kk != -1 && g.get_azelsim() == 0) {
//            d.dtext(16.0, 16.0, gg, Color.red, "comerr j=" + j + " n=" + n);
//            g.set_comerr(g.get_comerr() + 1);
//            if (g.get_fstatus() == 1)
//                o.stroutfile(g, "* ERROR comerr on cal");
//            return;
//        }
//        d.dtext(16.0, 80.0, gg, Color.black, "recv " + str);
//        return;
//    }
//
//
//    void vazel(double az, double el, global g, disp d, Graphics gg, outfile o)
//        // command antenna movement
//    {
//        int i, k, kk, n, nn, count, rr, region1, region2, region3;
//        double scale, ell, azz, ra, dec, ha, north, west, zen, pole, rad, glat, glon, sec, x, y;
//        int j;
//        char m[] = new char[80]; /* avoid byte array compiler bug */
//        char recv[] = new char[80];
//        String str, str1, str2;
//        StringTokenizer parser;
//        count = 0;
//        d.dtext(670.0, 24.0, gg, Color.black, "cmd " + d.dc(az, 5, 1) + " " + d.dc(el, 5, 1) + " deg");
//        if (g.get_azelsim() == 0) {
//            str = "antenna drive status:";
//            if (g.get_comerr() > 0)
//                str += " comerr= " + g.get_comerr();
//        } else
//            str = "antenna drive simulated";
//        if (g.get_vsrt() == 0)
//            d.dtext(16.0, 32.0, gg, Color.black, str);
//        az = az % 360;          /* Fold into reasonable range */
//        if (g.get_south() == 0) {
//            az = az + 360.0;    /* put az in range 180 to 540 */
//            if (az > 540.0)
//                az -= 360.0;
//            if (az < 180.0)
//                az += 360.0;
//        }
//        region1 = region2 = region3 = 0;
//        if (az >= g.get_azlim1() && az < g.get_azlim2() && el >= g.get_ellim1()
//            && el <= g.get_ellim2())
//            region1 = 1;
//        if (az > g.get_azlim1() + 180.0 && el > (180.0 - g.get_ellim2()))
//            region2 = 1;
//        if (az < g.get_azlim2() - 180.0 && el > (180.0 - g.get_ellim2()))
//            region3 = 1;
//
//        north = Math.cos(az * Math.PI / 180.0) * Math.cos(el * Math.PI / 180.0);
//        west = -Math.sin(az * Math.PI / 180.0) * Math.cos(el * Math.PI / 180.0);
//        zen = Math.sin(el * Math.PI / 180.0);
//        pole = north * Math.cos(g.get_lat()) + zen * Math.sin(g.get_lat());
//        rad = zen * Math.cos(g.get_lat()) - north * Math.sin(g.get_lat());
//        dec = Math.atan2(pole, Math.sqrt(rad * rad + west * west));
//        ha = Math.atan2(west, rad);
//        ha = ha * 180.0 / Math.PI;
//
//        if ((region1 == 0 && region2 == 0 && region3 == 0) || ha > 64 || ha < -64) {
//            d.dtext(16.0, 48.0, gg, Color.red, "cmd out of limits");
//            d.set_bc(Color.black, 4);
//            if (g.get_fstatus() == 1 && g.get_track() != 0)
//                o.stroutfile(g, "* ERROR cmd out of limits");
//            g.set_track(0);
//            try {
//                Thread.sleep(100);
//                }
//            catch(InterruptedException e) {
//                System.out.println(e);
//            }
//            return;
//        }
//
//
//        scale = g.get_hacounts_per_deg();
//        g.set_slew(0);
//        count = (int) (ha * scale - g.get_azcount()); // use azcount for ha
//        if (g.get_stow() == 1)  // drive to stow
//            count = 9999;
//        if (count == 0)
//            rr = 1;             // forces plot after restore
//        else
//            rr = 0;
//        while (count != 0 || rr == 1) {
//            if (g.get_track() != -1 && rr == 0) {
//                g.set_slew(1);
//                d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: slewing   ");
//                d.set_bc(Color.black, 4);
//                d.set_bc(Color.black, 3);
//                x = g.get_xlast(500);
//                y = g.get_ylast(500);
//                if (x != g.get_xlast(0) || y != g.get_ylast(0)) {
//                    d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//                    d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//                }
//                x = (int) (g.get_azcmd() * 640.0 / 360.0);
//                if (g.get_south() == 0)
//                    x -= 320;
//                if (x < 0)
//                    x += 640;
//                if (x > 640)
//                    x -= 640;
//                y = (int) (ylim - g.get_elcmd() * (ylim - ylim0) / 90);
//                g.set_xlast(x, 500);
//                g.set_ylast(y, 500);
//                d.lpaint(gg, Color.yellow, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//                d.lpaint(gg, Color.yellow, (double) (x), (double) (y - 10), (double) (x), (double) (y + 10));
//                if (count >= 0) {
//                    str = "ACA1\r";
//                } else {
//                    str = "ACC1\r";
//                }
//                if (count == 9999) {
//                    str = "ACB1\r";
//                    azatstow = elatstow = 1;
//                    g.set_stow(1);
//                }
//
//                j = n = 0;
//                if (g.get_azelsim() != 0) {
//                    str2 = "\n";
//                    str2.getChars(0, str2.length(), recv, 0);
//                    recv[0] = 13;
//                    n = str2.length();
//                }
//                d.dtext(16.0, 64.0, gg, Color.black,
//                        "trans" + g.get_azelsim() + " " + str.substring(0, str.length() - 1) + "     ");
//                d.ppclear(gg, 16.0, 80.0, 180.0);
//                kk = -1;
//                if (g.get_azelsim() == 0) {
//                    try {
//                        serialPort.enableReceiveTimeout(100);
//                    }
//                    catch(UnsupportedCommOperationException e) {
//                        System.out.println(e);
//                    }
//                    try {
//                        outputStream.write(str.getBytes());
//                        j = n = kk = 0;
//                        while (kk >= 0 && kk < 3000) {
//                            d.ppclear(gg, 16.0, 48.0, 180.0);
//                            d.dtext(16.0, 48.0, gg, Color.black, "waiting on drive   " + kk);
//                            j = inputStream.read();
//                            kk++;
//                            if (j >= 0 && n < 80) {
//                                recv[n] = (char) j;
////               System.out.println("rec "+j);
//                                n++;
//                            }
//                            if ((n > 0 && j == -1) || j == 13)
//                                kk = -1; // end of message
//
//                            t.getTsec(g, d, gg);
//                        }
//                        d.ppclear(gg, 16.0, 48.0, 180.0);
//                    }
//                    catch(IOException e) {
//                        System.out.println(e);
//                    }
//                    // no need to close
//                    try {
//                        if (count != 9999 || g.get_azcount() == 0)
//                            Thread.sleep(2000);
//                        else {
//                            d.dtext(16.0, 48.0, gg, Color.black, "waiting 60s to ensure stow");
//                            Thread.sleep(60000);
//                            d.ppclear(gg, 16.0, 48.0, 180.0);
//                        }
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//                if (count != 9999) {
//                    if (count > 0) {
//                        g.set_azcount(1 + g.get_azcount());
//                        count--;
//                    } else {
//                        g.set_azcount(-1 + g.get_azcount());
//                        count++;
//                    }
//                    if (count == 0)
//                        g.set_slew(0);
//                } else {
//                    g.set_azcount(0);
//                    count = 0;
//                }
//                if (kk != -1) {
//                    d.dtext(16.0, 16.0, gg, Color.red,
//                            "comerr j=" + j + " n=" + n + " kk " + kk + "  " + count);
//                    g.set_comerr(g.get_comerr() + 1);
//                    if (g.get_fstatus() == 1)
//                        o.stroutfile(g, "* ERROR comerr");
//                    if (g.get_mainten() == 0)
//                        g.set_stow(1);
//                    return;
//                }
//
//                if (g.get_azelsim() != 0 && g.get_azelsim() < 10) {
//                    d.ppclear(gg, 16.0, 48.0, 180.0);
//                    try {
//                        Thread.sleep(100);
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//                str = String.copyValueOf(recv, 0, n - 1);
//                d.ppclear(gg, 16.0, 80.0, 180.0);
//                d.dtext(16.0, 80.0, gg, Color.black, "recv " + str);
//                if (g.get_azelsim() == 0) {
//                    try {
//                        Thread.sleep(5);
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//            }
//            if (g.get_track() != -1) {
//                if (g.get_slew() == 1)
//                    g.set_track(0);
//                else
//                    g.set_track(1);
//            }
//            ha = g.get_azcount() / scale;
//            azz = geom.get_radec_az(ha * Math.PI / 180.0, g.get_mount_dec() * Math.PI / 180.0, g.get_lat());
//            ell = geom.get_radec_el();
//            g.set_aznow(azz * 180.0 / Math.PI);
//            if (g.get_aznow() > 360.0)
//                g.set_aznow(g.get_aznow() - 360.0);
//            g.set_elnow(ell * 180.0 / Math.PI);
//            d.dtext(670.0, 40.0, gg, Color.black,
//                    "azel  " + d.dc(g.get_aznow(), 5, 1) + " " + d.dc(g.get_elnow(), 5, 1) + " deg");
//            d.dtext(670.0, 56.0, gg, Color.black, "MOUNT LHA " + d.dc(ha, 5, 1) + " deg");
//            x = g.get_xlast(0);
//            y = g.get_ylast(0);
//            d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//            d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//            x = (int) (g.get_aznow() * 640.0 / 360.0);
//            if (g.get_south() == 0) {
//                x -= 320;
//                if (x < 0)
//                    x += 640;
//            }
//            y = (int) (ylim - g.get_elnow() * (ylim - ylim0) / 90);
//            g.set_xlast(x, 0);
//            g.set_ylast(y, 0);
//            d.lpaint(gg, Color.red, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//            d.lpaint(gg, Color.red, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//            if (Math.abs(g.get_aznow() - g.get_azstow()) < 0.1
//                && Math.abs(g.get_elnow() - g.get_elstow()) < 0.1) {
//                d.set_bc(Color.green, 3);
//                d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: at stow");
//                g.set_stow(-1); // at stow
//
//            } else {
//                d.set_bc(Color.black, 3);
//                if (g.get_stow() == -1)
//                    g.set_stow(0);
//            }
//            if (g.get_stow() != 0) {
//                g.set_track(0);
//            }
//            sec = (double) t.getTsec(g, d, gg);
//            ra = geom.get_galactic_ra(sec, g.get_aznow(), g.get_elnow(), g, t);
//            dec = geom.get_galactic_dec();
//            glat = geom.get_galactic_glat();
//            glon = geom.get_galactic_glon();
//            g.set_glat(glat);
//            g.set_glon(glon);
//            d.dtext(670.0, 120.0, gg, Color.black,
//                    "radec " + d.dc(ra, 5, 1) + " hrs " + d.dc(dec, 5, 1) + " deg");
//            d.dtext(670.0, 104.0, gg, Color.black, "Galactic l ="
//                    + d.dc(glon, 4, 0) + " b =" + d.dc(glat, 3, 0));
//            d.lpaint(gg, Color.black, 0.0, 85.0, 217.0, 85.0);
//            d.stext(16.0, ylim + 22.0, gg, Color.black,
//                    g.get_statnam() + " lat " + d.dc(g.get_lat() * 180.0 / Math.PI, 4, 1) +
//                    " lonw " + d.dc(g.get_lon() * 180.0 / Math.PI, 4, 1));
//            d.lpaint(gg, Color.black, 0.0, 0.0, 217.0, 0.0);
//            rr = 0;
//        }
//        return;
//    }
//
//
//    void vazel2(double az, double el, global g, disp d, Graphics gg, outfile o)
//        // command antenna movement
//    {
//        int i, k, kk, n, ax, nax, nn, azcount, elcount, region1, region2, region3;
//        double scaleaz, scaleel, ell, azz, a, ra, dec, ha, north, west, zen, pole, rad, glat, glon, sec, x, y;
//        int j, isend;
//        char m[] = new char[80]; /* avoid byte array compiler bug */
//        char recv[] = new char[80];
//        String str, str1, str2;
//        StringTokenizer parser;
//        azcount = elcount = 0;
//        d.dtext(670.0, 24.0, gg, Color.black, "cmd " + d.dc(az, 5, 1) + " " + d.dc(el, 5, 1) + " deg");
//        if (g.get_azelsim() == 0) {
//            str = "antenna drive status:";
//            if (g.get_comerr() > 0)
//                str += " comerr= " + g.get_comerr();
//        } else
//            str = "antenna drive simulated";
//        if (g.get_vsrt() == 0)
//            d.dtext(16.0, 32.0, gg, Color.black, str);
//        az = az % 360;          /* Fold into reasonable range */
//        if (g.get_south() == 0) {
//            az = az + 360.0;    /* put az in range 180 to 540 */
//            if (az > 540.0)
//                az -= 360.0;
//            if (az < 180.0)
//                az += 360.0;
//        }
//        region1 = region2 = region3 = 0;
//        if (az >= g.get_azlim1() && az < g.get_azlim2() && el >= g.get_ellim1()
//            && el <= g.get_ellim2())
//            region1 = 1;
//        if (az > g.get_azlim1() + 180.0 && el > (180.0 - g.get_ellim2()))
//            region2 = 1;
//        if (az < g.get_azlim2() - 180.0 && el > (180.0 - g.get_ellim2()))
//            region3 = 1;
//
//        if (region1 == 0 && region2 == 0 && region3 == 0) {
//            d.dtext(16.0, 48.0, gg, Color.red, "cmd out of limits");
//            d.set_bc(Color.black, 4);
//            if (g.get_fstatus() == 1 && g.get_track() != 0)
//                o.stroutfile(g, "* ERROR cmd out of limits");
//            g.set_track(0);
//            try {
//                Thread.sleep(100);
//            }
//            catch(InterruptedException e) {
//                System.out.println(e);
//            }
//            return;
//        }
//
//
//        scaleaz = g.get_azcounts_per_deg();
//        scaleel = g.get_elcounts_per_deg();
//        azz = az - g.get_azstow() + g.get_azcor();
//        ell = el - g.get_ellim1() + g.get_elcor();
//        g.set_slew(0);
//
//        a = azz * scaleaz - g.get_azcount();
//        if (a > 0)
//            azcount = (int) (a + 0.49); // 0.49 to prevent hunting
//        else
//            azcount = (int) (a - 0.49); // due to fp precision
//
//        a = ell * scaleel - g.get_elcount();
//        if (a > 0)
//            elcount = (int) (a + 0.49);
//        else
//            elcount = (int) (a - 0.49);
//
//        if (g.get_stow() == 1)  // drive to stow
//            azcount = 9999;
//        if (g.get_track() != -1 && (azcount != 0 || elcount != 0)) {
//            g.set_slew(1);
//            d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: slewing   ");
//            d.set_bc(Color.black, 4);
//            d.set_bc(Color.black, 3);
//            x = g.get_xlast(500);
//            y = g.get_ylast(500);
//            if (x != g.get_xlast(0) || y != g.get_ylast(0)) {
//                d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//                d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//            }
//            x = (int) (g.get_azcmd() * 640.0 / 360.0);
//            if (g.get_south() == 0)
//                x -= 320;
//            if (x < 0)
//                x += 640;
//            if (x > 640)
//                x -= 640;
//            y = (int) (ylim - g.get_elcmd() * (ylim - ylim0) / 90);
//            g.set_xlast(x, 500);
//            g.set_ylast(y, 500);
//            d.lpaint(gg, Color.yellow, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//            d.lpaint(gg, Color.yellow, (double) (x), (double) (y - 10), (double) (x), (double) (y + 10));
//            if (azcount != 0 && elcount != 0 && azcount != 9999)
//                nax = 2;
//            else
//                nax = 1;
//            for (ax = 0; ax < nax; ax++) {
//                isend = 0;
//                if (ax == 0 || nax == 1) {
//                    if (azcount > 0) {
//                        str = "ACC1\r";
//                        isend = 1;
//                        }
//                    if (azcount < 0) {
//                        str = "ACA1\r";
//                        isend = 2;
//                       }
//                }
//                if (ax == 1 || nax == 1) {
//                    if (elcount > 0) {
//                        str = "ACD1\r";
//                        isend = 3;
//                        }
//                    if (elcount < 0) {
//                        str = "ACE1\r";
//                        isend = 4;
//                        }
//                }
//
//                if (azcount == 9999) {
//                    str = "ACB1\r";
//                    azatstow = elatstow = 1;
//                    g.set_stow(1);
//                }
//
//                j = n = 0;
//                if (g.get_azelsim() != 0) {
//                    str2 = "\n";
//                    str2.getChars(0, str2.length(), recv, 0);
//                    recv[0] = 13;
//                    n = str2.length();
//                }
//                d.dtext(16.0, 64.0, gg, Color.black,
//                        "trans" + g.get_azelsim() + " " + str.substring(0, str.length() - 1) + "     ");
//                d.ppclear(gg, 16.0, 80.0, 180.0);
//                kk = -1;
//                if (g.get_azelsim() == 0) {
//                    try {
//                        serialPort.enableReceiveTimeout(100);
//                    }
//                    catch(UnsupportedCommOperationException e) {
//                        System.out.println(e);
//                    }
//                    try {
//                        outputStream.write(str.getBytes());
//                        j = n = kk = 0;
//                        while (kk >= 0 && kk < 3000) {
//                            d.ppclear(gg, 16.0, 48.0, 180.0);
//                            d.dtext(16.0, 48.0, gg, Color.black, "waiting on drive   " + kk);
//                            j = inputStream.read();
//                            kk++;
//                            if (j >= 0 && n < 80) {
//                                recv[n] = (char) j;
////               System.out.println("rec "+j);
//                                n++;
//                            }
//                            if ((n > 0 && j == -1) || j == 13)
//                                kk = -1; // end of message
//
//                            t.getTsec(g, d, gg);
//                        }
//                        d.ppclear(gg, 16.0, 48.0, 180.0);
//                    }
//                    catch(IOException e) {
//                        System.out.println(e);
//                    }
//                    // no need to close
//                    try {
//                        if (azcount != 9999 || g.get_azcount() == 0)
//                            Thread.sleep(2000);
//                        else {
//                            d.dtext(16.0, 48.0, gg, Color.black, "waiting 60s to ensure stow");
//                            Thread.sleep(60000);
//                            d.ppclear(gg, 16.0, 48.0, 180.0);
//                        }
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//                if (azcount != 9999) {
//                        if (isend == 1) {
//                            g.set_azcount(1 + g.get_azcount());
//                            azcount--;
//                        }
//                        if (isend == 2) {
//                            g.set_azcount(-1 + g.get_azcount());
//                            azcount++;
//                        }
//                        if (isend == 3) {
//                            g.set_elcount(1 + g.get_elcount());
//                            elcount--;
//                        }
//                        if (isend == 4) {
//                            g.set_elcount(-1 + g.get_elcount());
//                            elcount++;
//                        }
//                        if (azcount == 0 && elcount == 0)
//                            g.set_slew(0);
//                } else {
//                    g.set_azcount(0);
//                    g.set_elcount(0);
//                    azcount = 0;
//                    elcount = 0;
//                }
//                if (kk != -1) {
//                    d.dtext(16.0, 16.0, gg, Color.red,
//                            "comerr j=" + j + " n=" + n + " kk " + kk + "  " + azcount);
//                    g.set_comerr(g.get_comerr() + 1);
//                    if (g.get_fstatus() == 1)
//                        o.stroutfile(g, "* ERROR comerr");
//                    if (g.get_mainten() == 0)
//                        g.set_stow(1);
//                    return;
//                }
//
//                if (g.get_azelsim() != 0 && g.get_azelsim() < 10) {
//                    try {
//                        Thread.sleep(100);
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//                str = String.copyValueOf(recv, 0, n - 1);
//                d.ppclear(gg, 16.0, 80.0, 180.0);
//                d.dtext(16.0, 80.0, gg, Color.black, "recv " + str);
//                if (g.get_azelsim() == 0) {
//                    try {
//                        Thread.sleep(1);
//                    }
//                    catch(InterruptedException e) {
//                        System.out.println(e);
//                    }
//                }
//            }
//        }
//        if (g.get_track() != -1) {
//            if (g.get_slew() == 1)
//                g.set_track(0);
//            else
//                g.set_track(1);
//        }
//        azz = g.get_azcount() / scaleaz + g.get_azstow() - g.get_azcor();
//        ell = g.get_elcount() / scaleel + g.get_ellim1() - g.get_elcor();
//        g.set_aznow(azz);
//        if (g.get_aznow() > 360.0)
//            g.set_aznow(g.get_aznow() - 360.0);
//        g.set_elnow(ell);
//        d.dtext(670.0, 40.0, gg, Color.black,
//                "azel  " + d.dc(g.get_aznow(), 5, 1) + " " + d.dc(g.get_elnow(), 5, 1) + " deg");
//        x = g.get_xlast(0);
//        y = g.get_ylast(0);
//        d.lpaint(gg, Color.white, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//        d.lpaint(gg, Color.white, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//        x = (int) (g.get_aznow() * 640.0 / 360.0);
//        if (g.get_south() == 0) {
//            x -= 320;
//            if (x < 0)
//                x += 640;
//        }
//        y = (int) (ylim - g.get_elnow() * (ylim - ylim0) / 90);
//        g.set_xlast(x, 0);
//        g.set_ylast(y, 0);
//        d.lpaint(gg, Color.red, (double) (x - 10), (double) y, (double) (x + 10), (double) y);
//        d.lpaint(gg, Color.red, (double) x, (double) (y - 10), (double) x, (double) (y + 10));
//        if (Math.abs(g.get_aznow() - g.get_azstow()) < 0.1 && Math.abs(g.get_elnow() - g.get_elstow()) < 0.1) {
//            d.set_bc(Color.green, 3);
//            d.dtext(340.0, ylim + 40.0, gg, Color.black, "Status: at stow");
//            g.set_stow(-1);     // at stow
//
//        } else {
//            d.set_bc(Color.black, 3);
//            if (g.get_stow() == -1)
//                g.set_stow(0);
//        }
//        if (g.get_stow() != 0) {
//            g.set_track(0);
//        }
//        sec = (double) t.getTsec(g, d, gg);
//        ra = geom.get_galactic_ra(sec, g.get_aznow(), g.get_elnow(), g, t);
//        dec = geom.get_galactic_dec();
//        glat = geom.get_galactic_glat();
//        glon = geom.get_galactic_glon();
//        g.set_glat(glat);
//        g.set_glon(glon);
//        d.dtext(670.0, 120.0, gg, Color.black,
//                "radec " + d.dc(ra, 5, 1) + " hrs " + d.dc(dec, 5, 1) + " deg");
//        d.dtext(670.0, 104.0, gg, Color.black, "Galactic l =" + d.dc(glon, 4, 0) + " b =" + d.dc(glat, 3, 0));
//        d.lpaint(gg, Color.black, 0.0, 85.0, 217.0, 85.0);
//        d.stext(16.0, ylim + 22.0, gg, Color.black,
//                g.get_statnam() + " lat " + d.dc(g.get_lat() * 180.0 / Math.PI, 4, 1) +
//                " lonw " + d.dc(g.get_lon() * 180.0 / Math.PI, 4, 1));
//        d.lpaint(gg, Color.black, 0.0, 0.0, 217.0, 0.0);
//        return;
//    }

    void close(Global g) {
        if ((g.get_azelsim() == 0 || g.get_radiosim() == 0)
           && (g.get_azelsim() == 0 || g.get_vsrt() == 0))
            serialPort.close();
    }
    
    public static void main(String[] args) {
    	
    	System.out.println("SRTDevice debugger");
    	SrtDevice dev = new SrtDevice();
    	dev.azel2(0, 5000);    	
    }
}



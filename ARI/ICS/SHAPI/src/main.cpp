// Author: Justin Crooks
// Test Equipment Plus
// Date: July 14, 2011

// Revision History:
// 7/14/11 Created.

//This is a simple C++ program to exercise the Signal Hound through the Linux API.

#include <iostream>
#include <sys/time.h>
#include <sys/resource.h>
#include <fstream>

#include "CUSBSA.h"
using namespace std;

int set_realtime_priority() {
  int ret = 0;
  pthread_t this_thread = pthread_self();
  
  struct sched_param params;
  params.sched_priority = sched_get_priority_max(SCHED_FIFO);
  return pthread_setschedparam(this_thread, SCHED_FIFO, &params);
}

#define CHECK_STATUS(label, function)		\
  if(function) {				\
    cout << label << " failed\n";		\
  } else {					\
    cout << label << " success\n";		\
  }

double find_max(double *p, int len, int *ix = 0)
{
  double max = -1000.0;

  for(int i = 0; i < len; i++) {
    if(p[i] > max) {
      max = p[i];
      if(ix) {
	*ix = i;
      }
    }    
  }
  return max;
}

int main()
{
  //if(set_realtime_priority()) {
  // cout << "Unable to set real-time thread prio\n";
  // return 0;
  //}

    CUSBSA mySignalHound;
    int count;

    cout << "Initializing\n";
    CHECK_STATUS("Initialize():", mySignalHound.Initialize(0));

    ofstream file("trace.plot");

    // Max Check
    for(int i = 0; i < 1; i++) {
      double max = 0.0;
      int max_ix = 0;

      count = mySignalHound.FastSweep(310.0e6, 390.0e6);
      max = find_max(mySignalHound.dTraceAmpl, count, &max_ix);
      cout << "Sweep " << i << " max = " << max;
      cout << " max index = " << max_ix << endl;

      usleep(50000);
      for(int i = 0; i < count; i++)
      cout << mySignalHound.dTraceFreq[i] << " "
           << mySignalHound.dTraceAmpl[i] << endl;
      cout << endl;

      cout << "size " << count << endl;
    }

    return 0;
}


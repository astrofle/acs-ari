%module CUSBSA
%{
#include "CUSBSA.h"
%}

%ignore CUSBSA::GetRBW();
%include "CUSBSA.h"


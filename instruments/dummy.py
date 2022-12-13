# -*- coding: utf-8 -*-
"""
Module to serve as dummy. The dummy instrument can read/write values.
The latency option determines the time it takes for the dummy instrument to 
'respond' to the main python code. Default = 1 ms.

The response of the device is zero by default, and takes on write_val values instantly.

Version 1.0 (2022-12-12)
Daan Wielens - Researcher
University of Twente
d.h.wielens@utwente.nl
"""

import time

class dummy:
    type = 'Dummy'
    def __init__(self):
        self.time = time
        self.latency = 1e-3
        self.value = 0

    def read_val(self):
        time.sleep(self.latency)
        return self.value
    
    def write_val(self, val):
        time.sleep(self.latency)
        self.value = val
        
    # A 'slow' value takes 10 latency time units.    
    def read_slowval(self):
        time.sleep(self.latency * 10)
        return self.value
        
    def write_slowval(self, val):
        time.sleep(self.latency * 10)
        self.value = val

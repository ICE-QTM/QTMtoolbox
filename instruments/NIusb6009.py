# -*- coding: utf-8 -*-
"""
Module to interact with a NI USB-6009.
Requirements:
    - Downloading NI-DAQmx 2023 Q2 (download at NI site)
    - pip install nidaqmx

Version 1.0 (2023-05-09)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl
"""

import nidaqmx

class NIusb6009:
    type = 'NI USB-6009'

    def __init__(self, DEVname='Dev1'):
        self.DEVname = DEVname
        self.ao0_out = 0
        self.ao1_out = 0
    
    def read_ai0(self):
        # Differential input: 14 bit resolution, [-10, 10 V] --> 1.22 mV
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.DEVname + r'/ai0')
            return task.read()

    def read_ai1(self):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.DEVname + r'/ai1')
            return task.read()

    def read_ai2(self):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.DEVname + r'/ai2')
            return task.read()
        
    def read_ai3(self):
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(self.DEVname + r'/ai3')
            return task.read()

    def write_ao0(self, val):
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(self.DEVname + r'/ao0', min_val = 0, max_val = 5)
            task.write(val)
            task.wait_until_done()
            task.stop()
            self.ao0_out = val
            
    def read_ao0(self):
        # Note: this function returns the setpoint, since we can't measure the actual output voltage!
        return self.ao0_out
    
    def write_ao1(self, val):
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(self.DEVname + r'/ao1', min_val = 0, max_val = 5)
            task.write(val)
            task.wait_until_done()
            task.stop()
            self.ao1_out = val
            
    def read_ao1(self):
        # Note: this function returns the setpoint, since we can't measure the actual output voltage!
        return self.ao1_out
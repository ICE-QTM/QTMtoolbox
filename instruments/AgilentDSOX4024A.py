# -*- coding: utf-8 -*-
"""
Module to interact with a Agilent DSO-X 4024A oscilloscope.
Uses pyVISA to communicate with the USB device.
--- If GPIB is used, modify the __init__ section of the class. ---

Version 1.0 (2022-03-21)
Daan Wielens - Researcher at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa
import ast
import numpy as np
from struct import unpack

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Agilent DSO-X 4024A series. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class AgilentDSOX4024A:
    type = 'AgilentDSOX4024A'

    def __init__(self, USBaddr='USB0::0x0957::0x17A6::MY54230477::INSTR'):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource(USBaddr)
        # Check if device is really a Agilent 33220A series
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if not '4024A' in model:
            raise WrongInstrErr('Expected Agilent DSO-X 4024A series, got {}'.format(resp))
        self.visa.timeout = 10000

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp
    
    def query(self, val):
        resp = self.visa.query(val).strip('\n')
        return resp

    def write(self, val):
        self.visa.write(val)

    def close(self):
        self.visa.close()

    def read_acqtype(self):
        resp = self.visa.query(':ACQ:TYPE?')
        return resp.strip('\n')
    
    def write_acqtype(self, val):
        if val in ['NORM', 'AVER', 'HRES', 'PEAK']:
            self.visa.write(':ACQ:TYPE ' + val)
            
    def read_avgnpts(self):
        resp = self.visa.query(':ACQ:COUN?')
        return int(resp.strip('\n'))
    
    def write_avgnpts(self, val):
        if val >= 2 and val <= 65536:
            self.visa.write(':ACQ:COUN ' + str(val))
    
    def read_x1min(self):
        return float(self.get_preamble1()[5])
            
    def read_x1max(self):
        x1min = self.read_x1min()
        x1inc = float(self.get_preamble1()[4])
        x1ref = float(self.get_preamble1()[6])
        npts = int(self.get_preamble1()[2])
        return (npts-1-x1ref)*x1inc + x1min # Prog. manual page 1432
    
    def get_pre1(self):
        self.visa.write('WAV:SOUR CHAN1')
        self.visa.write('WAV:PRE?')
        preamble: bytes = self.visa.read_raw()
        preamble: tuple = ast.literal_eval(preamble.decode())
        yinc = preamble[7]
        yorg = preamble[8]
        yref = preamble[9]
        xinc = preamble[4]
        return yinc, yorg, yref, xinc
    
    def get_wav1(self, npts=500):
        # Get preamble
        pre = self.get_pre1()
        
        # Set data format, begin output
            # While the BYTE format only returns 8-bit values (0-255), the WORD format
            # returns 16-bit values (0-65535), which thus captures the full 12-bit 
             # resolution of the scope.
        self.visa.write(":WAVeform:FORMat WORD") # Word = 2x 8-bit values
        self.visa.write('WAV:BYT LSBF') # Windows = little-endian (least significant byte first)
        self.visa.write(":WAVeform:POINts " + str(npts))
        self.visa.write(":WAVeform:DATA?")
        
        # Read output and convert from binary to data
        data = self.visa.read_raw()
        ADCwave = data[10:-1]
        ADCwave = np.array(unpack('%sH' % int(len(ADCwave)/2), ADCwave)) # Unpack into unsigned short. len()/2 since every value now takes two bits 
        
        # Convert data to scale
        V = (ADCwave - pre[2]) * pre[0]
        t = np.arange(0, pre[3] * len(V), pre[3])
        return t, V
    
    def get_pre2(self):
        self.visa.write('WAV:SOUR CHAN2')
        self.visa.write('WAV:PRE?')
        preamble: bytes = self.visa.read_raw()
        preamble: tuple = ast.literal_eval(preamble.decode())
        yinc = preamble[7]
        yorg = preamble[8]
        yref = preamble[9]
        xinc = preamble[4]
        return yinc, yorg, yref, xinc
    
    def get_wav2(self, npts=500):
        # Get preamble
        pre = self.get_pre2()
        
        # Set data format, begin output
        self.visa.write(":WAVeform:FORMat WORD") 
        self.visa.write('WAV:BYT LSBF') 
        self.visa.write(":WAVeform:POINts " + str(npts))
        self.visa.write(":WAVeform:DATA?")
        
        # Read output and convert from binary to data
        data = self.visa.read_raw()
        ADCwave = data[10:-1]
        ADCwave = np.array(unpack('%sH' % int(len(ADCwave)/2), ADCwave)) 
        
        # Convert data to scale
        V = (ADCwave - pre[2]) * pre[0]
        t = np.arange(0, pre[3] * len(V), pre[3])
        return t, V
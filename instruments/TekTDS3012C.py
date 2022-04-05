# -*- coding: utf-8 -*-
"""
Module to interact with a Tektronix AFG1022.
Uses pyVISA to communicate with the USB/GPIB device.

Version 2.0 (2022-04-05)
Daan Wielens - Researcher at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import pyvisa as visa
import numpy as np
import ast
from struct import unpack

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Tektronix TDS 3012 series. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class TekTDS3012C:
    type = 'Tektronix TDS 3012C'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Tektronix AFG1022
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if 'TDS 3012' not in model:
            raise WrongInstrErr('Expected Tektronix TDS 3012 series, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()
        
    def query(self, val):
        return self.visa.query(val)
    
    def write(self, val):
        self.visa.write(val)

    # Read measurements
    def read_meas1(self):
        resp = self.query('MEASU:MEAS1:VAL?')
        resp = float(resp.split(' ')[1])
        return resp

    def read_meas2(self):
        resp = self.query('MEASU:MEAS2:VAL?')
        resp = float(resp.split(' ')[1])
        return resp

    def read_meas3(self):
        resp = self.query('MEASU:MEAS3:VAL?')
        resp = float(resp.split(' ')[1])
        return resp

    def read_meas4(self):
        resp = self.query('MEASU:MEAS4:VAL?')
        resp = float(resp.split(' ')[1])
        return resp

    # Divider settings
    def write_horzdiv(self, val):
        val = float(val)
        self.write('HOR:MAI:SCA ' + str(val) + '\n')

    def write_vertdiv1(self, val):
        val = float(val)
        self.write('CH1:SCA ' + str(val) + '\n')

    def write_vertdiv2(self, val):
        val = float(val)
        self.write('CH2:SCA ' + str(val) + '\n')

    def read_horzdiv(self):
        return float(self.query('HOR:MAI:SCA?').strip('\n'))
    
    def read_vertdiv1(self):
        return float(self.query('CH1:SCA?').strip('\n'))
    
    def read_vertdiv2(self):
        return float(self.query('CH2:SCA?').strip('\n'))
    
    # Preamble acquisition
    def get_pre1(self):
        self.write('DATA:SOU CH1')
        data = self.query('WFMP?').split(';')
        ymult = float(data[12])
        yzero = float(data[13])
        yoff = float(data[14])
        xinc = float(data[8])
        return ymult, yzero, yoff, xinc
        
    def get_pre2(self):
        self.write('DATA:SOU CH2')
        data = self.query('WFMP?').split(';')
        ymult = float(data[12])
        yzero = float(data[13])
        yoff = float(data[14])
        xinc = float(data[8])
        return ymult, yzero, yoff, xinc   
    
    # Get number of points (horizontal resolution)
    def read_npts1(self):
        self.write('DATA:SOU CH1')
        return int(self.query('WFMP:NR_Pt?'))
        
    def read_npts2(self):
        self.write('DATA:SOU CH1')
        return int(self.query('WFMP:NR_Pt?'))
    
    def write_npts(self, val):
        if val in [500, 10000]:
            self.write('HOR:RECO ' + str(val))
        else:
            raise ValueError('The number of points can either be 500 or 10000.')
            
    # Get waveform
    def get_wav1(self):
        self.write('DATA:SOU CH1')
        # If 500 data points are chosen, the scope does 'fast trigger' / 1 bit data (256 bins)
        if self.read_npts1() == 500:
            self.write('DATA:WIDTH 1')
            self.write('DATA:ENC RPB') # Requires %sB for unpack
            pre = self.get_pre1()
            self.write('CURVE?')
            data = self.visa.read_raw()
             
            headerlen = 5 # We expect the header to be '#3500' (#, 3 bytes required to print the number 500, 500 itself; 1 bits per data point)
            ADCwave = data[headerlen:-1]
            ADCwave = np.array(unpack('%sB' % len(ADCwave), ADCwave))    
        # If 10000 points are chosen ('normal'), we get 2 bit data (65536 bins)
        else:
            self.write('DATA:WIDTH 2')
            self.write('DATA:ENC SRP') # Requires %sH for unpack
            pre = self.get_pre1()
            self.write('CURVE?')
            data = self.visa.read_raw()

            headerlen = 7 # '#520000' (#, 4 bytes for 10000*2, 20000 itself; 2 bits per data point)
            ADCwave = data[headerlen:-1]
            ADCwave = np.array(unpack('%sH' % int(len(ADCwave)/2), ADCwave))
         
        V = (ADCwave - pre[2]) * pre[0] + pre[1]
        t = np.arange(0, pre[3] * len(V), pre[3])
        return t, V       
     
    def get_wav2(self):
        self.write('DATA:SOU CH2')
        # If 500 data points are chosen, the scope does 'fast trigger' / 1 bit data (256 bins)
        if self.read_npts1() == 500:
            self.write('DATA:WIDTH 1')
            self.write('DATA:ENC RPB') # Requires %sB for unpack
            pre = self.get_pre2()
            self.write('CURVE?')
            data = self.visa.read_raw()
             
            headerlen = 5 # We expect the header to be '#3500' (#, 3 bytes required to print the number 500, 500 itself; 1 bits per data point)
            ADCwave = data[headerlen:-1]
            ADCwave = np.array(unpack('%sB' % len(ADCwave), ADCwave))    
        # If 10000 points are chosen ('normal'), we get 2 bit data (65536 bins)
        else:
            self.write('DATA:WIDTH 2')
            self.write('DATA:ENC SRP') # Requires %sH for unpack
            pre = self.get_pre2()
            self.write('CURVE?')
            data = self.visa.read_raw()

            headerlen = 7 # '#520000' (#, 4 bytes for 10000*2, 20000 itself; 2 bits per data point)
            ADCwave = data[headerlen:-1]
            ADCwave = np.array(unpack('%sH' % int(len(ADCwave)/2), ADCwave))
         
        V = (ADCwave - pre[2]) * pre[0] + pre[1]
        t = np.arange(0, pre[3] * len(V), pre[3])
        return t, V 

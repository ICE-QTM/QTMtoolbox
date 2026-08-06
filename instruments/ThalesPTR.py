# -*- coding: utf-8 -*-
"""
Module to interact with a Thales PTR controller (XPCDE4865/X).
Uses a serial connection to communicate with the device.

Version 2.0 (2026-08-06)
Daan Wielens - Researcher at ICE/QTM
University of Twente

New in V2.0: updated temperature conversion to use polynomial fit on data instead of linear approximation.

<!> For other users / labs: please update the thermometry fitting parameters for your sensor!
"""

import serial
import numpy as np

# --- Thermometry conversion constants ---
'''
For the thermometry conversion we use 4th-order polynomials to fit T(V) and V(T)
Fit equation: y = a + b*x + c*x^2 + d*x^3 + e*x^4
'''
# Volts to Kelvin
aVK = 418.15618
bVK = 359.35795
cVK = -1743.62202
dVK = 1700.28623
eVK = -635.4725

# Kelvin to Volts
aKV = 1.14512
bKV = -0.00113
cKV = -3.91435E-6
dKV = 4.6483E-9
eKV = 8.22724E-15

class ThalesPTR:
    type = 'Thales PTR cooler'
    
    def mVtoK(self, Vsensor):
        x = Vsensor / 1e3 # Convert from mV to V
        Tsensor = aVK + bVK*x + cVK*x**2 + dVK*x**3 + eVK*x**4 
        return Tsensor

    def KtomV(self, temp):
        Vsensor = aKV + bKV*temp + cKV*temp**2 + dKV*temp**3 + eKV*temp**4
        return Vsensor * 1e3 # Convert from V to mV
    
    def __init__(self, COMport=3):
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM' + str(COMport)
        self.ser.stopbits = 1
        self.ser.bytesize = 8
        self.ser.timeout = 1
        
    def query(self, val):
        self.ser.open()
        self.ser.write((val + '\r').encode())
        resp = self.ser.readline().decode().strip('\r\n')
        self.ser.close()
        return resp
    
    def write(self, val):
        self.ser.open()
        self.ser.write((val + '\r').encode())
        self.ser.readline().decode() # The device always gives a reply, so always catch it.
        self.ser.close()

    def read_Vsetp(self):
        return float(self.query('RSP'))
    
    def read_Vsensor(self):
        return float(self.query('RVS'))
    
    def read_Vac(self):
        return float(self.query('RVA'))
    
    def read_Vdc(self):
        return float(self.query('RVD'))
    
    def read_freq(self):
        return float(self.query('RFR'))
    
    def read_remote(self):
        return int(self.query('RRE'))
    
    def read_temp(self):
        return self.mVtoK(self.read_Vsensor())
    
    def read_Tsetp(self):
        return self.mVtoK(self.read_Vsetp())
    
    def write_Vsetp(self, val):
        if val >= 0.2 and val <= 5000:
            self.write('SSP ' + str(np.round(val, 3)))
        else:
            raise ValueError('Voltage setpoint [mV] needs to be within 0.2 and 5000 mV')
            
    def write_remote(self, val):
        if val == 0 or val == 1:
            self.write('SRE ' + str(val))
            
    def write_Tsetp(self, val):
        # This check ensures that the temperatures are within the allowed range
        if val >= 50 and val <= 300:
            # This furthermore will ensure that the voltage setpoint is within range of the controller 
            self.write_Vsetp(self.KtomV(val))
        else:
            raise ValueError('Temperature setpoint [K] needs to be within 50 and 300 K.')
        

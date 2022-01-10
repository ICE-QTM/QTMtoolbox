# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 2000 Multimeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.1 (2022-01-10)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import pyvisa as visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 2000 Multimeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keithley2000:
    type = 'Keithley 2000 Multimeter'
    
    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Keithley 2000
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != 'MODEL 2000':
            raise WrongInstrErr('Expected Keithley 2000, got {}'.format(resp))      
    
    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp
    
    def query(self, val):
        resp = str(self.visa.query(val))
        return resp
    
    def close(self):
        self.visa.close()
        
    def read_dcv(self):
        resp = float(self.visa.query('SENS:DATA?'))
        return resp
    
    def read_v(self):
        return float(self.visa.query('READ?'))
    
    def read_avgtype(self):
        return self.visa.query('VOLT:DC:AVER:TCON?').strip('\n')
    
    def write_avgtype(self, val):
        if val in ['MOV', 'REP']:
            resp = self.visa.write('VOLT:DC:AVER:TCON ' + val)
        else:
            raise ValueError('The averaging type should be "MOV" (moving) or "REP" (repeating).')
        
    def read_avgcount(self):
        return self.visa.query('VOLT:DC:AVER:COUN?').strip('\n')
    
    def write_avgcount(self, val):
        if int(val) >= 1 and int(val) <= 100:
            resp = self.visa.write('VOLT:DC:AVER:COUN ' + str(val))
        else:
            raise ValueError('The filter count should lie within 1 - 100.')
            
    def read_avgstate(self):
        return self.visa.query('VOLT:DC:AVER:STAT?').strip('\n')
    
    def write_avgstate(self, val):
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('VOLT:DC:AVER:STAT ON')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('VOLT:DC:AVER:STAT OFF')
        else:
            raise ValueError('This is not a valid state.')

    def read_avgnplc(self):
        return float(self.visa.query('VOLT:DC:NPLC?').strip('\n'))
    
    def write_avgnplc(self, val):
        if float(val) >= 0.01 and float(val) <= 10:
            resp = self.visa.write('VOLT:DC:NPLC ' + str(val))
        else:
            raise ValueError('The filter count should lie within 0.01 - 10.') 
            
    def read_conttrig(self):
        return float(self.visa.query('INIT:CONT?').strip('\n'))
    
    def write_conttrig(self, val):
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('INIT:CONT ON')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('INIT:CONT OFF')
        else:
            raise ValueError('This is not a valid state.')             

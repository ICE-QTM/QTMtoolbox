# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 2182A Nanovoltmeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.1 (2024-10-18)
Daan Wielens - Researcher at ICE/QTM
University of Twente
"""

import visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 2182A Nanovoltmeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keithley2182A:
    type = 'Keithley 2182A Nanovoltmeter'
    
    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Keithley 2182
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != 'MODEL 2182A':
            raise WrongInstrErr('Expected Keithley 2182A, got {}'.format(resp))      
    
    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp
    
    def close(self):
        self.visa.close()
        
    def read_dcv(self):
        resp = float(self.visa.query('SENS:DATA:FRES?'))
        return resp
    
    def read_v(self):
        return float(self.visa.query('READ?'))
    
    def read_avgtype(self):
        return self.visa.query('SENS:VOLT:DC:DFIL:TCON?').strip('\n')
    
    def write_avgtype(self, val):
        if val in ['MOV', 'REP']:
            resp = self.visa.write('SENS:VOLT:DC:DFIL:TCON ' + val)
        else:
            raise ValueError('The averaging type should be "MOV" (moving) or "REP" (repeating).')
        
    def read_avgcount(self):
        return self.visa.query('SENS:VOLT:DC:DFIL:COUN?').strip('\n')
    
    def write_avgcount(self, val):
        if int(val) >= 1 and int(val) <= 100:
            resp = self.visa.write('SENS:VOLT:DC:DFIL:COUN ' + str(val))
        else:
            raise ValueError('The filter count should lie within 1 - 100.')
            
    def read_avgstate(self):
        return self.visa.query('SENS:VOLT:DC:DFIL?').strip('\n')
    
    def write_avgstate(self, val):
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('SENS:VOLT:DC:DFIL ON')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('SENS:VOLT:DC:DFIL OFF')
        else:
            raise ValueError('This is not a valid state.')

    def read_avgnplc(self):
        return float(self.visa.query('SENS:VOLT:DC:NPLC?').strip('\n'))
    
    def write_avgnplc(self, val):
        if float(val) >= 0.01 and float(val) <= 10:
            resp = self.visa.write('SENS:VOLT:DC:NPLC ' + str(val))
        else:
            raise ValueError('The filter count should lie within 0.01 - 10.')
    
    def read_conttrig(self): #todo
        return float(self.visa.query('INIT:CONT?').strip('\n'))
    
    def write_conttrig(self, val): #todo
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('INIT:CONT ON')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('INIT:CONT OFF')
        else:
            raise ValueError('This is not a valid state.')
            
    def write_autorange(self):
        self.visa.write('SENS:VOLT:RANG:AUTO ON')
        

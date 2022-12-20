# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 6500 Multimeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.1 (2022-12-20)
Daan Wielens - Researcher at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import pyvisa as visa
import time

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 6500 Multimeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keithley6500:
    type = 'Keithley 6500 Multimeter'
    
    def __init__(self, addr, type='GPIB'):
        rm = visa.ResourceManager()
        if type == 'GPIB':
            self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(addr))
        elif type == 'USB':
            self.visa = rm.open_resource(addr)
        else:
            raise ValueError('Connections can either be made via USB or GPIB at the moment.')
        # Check if device is really a Keithley 2000
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != 'MODEL DMM6500':
            raise WrongInstrErr('Expected Keithley 6500, got {}'.format(resp)) 
        # Increase timeout, because changing mode (i.e. read_dcv(), then read_acv()) takes time for to initialize
        self.visa.timeout = 5000
        # Beep for measurement
        self.notify = False
    
    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp
    
    def query(self, val):
        resp = str(self.visa.query(val))
        return resp
    
    def write(self, val):
        self.visa.write(val)
    
    def close(self):
        self.visa.close()
        
    def beep(self, frequency, duration):
        self.visa.write('SYST:BEEP ' + str(frequency) + ', ' + str(duration))
        time.sleep(duration + 0.02)
        
    # Use the current measurement mode and return one reading
    def read(self):
        if self.notify:
            self.beep(1569.98, 0.05)
            self.beep(2093, 0.1)
        return float(self.query('READ?'))
    
    # Set the device to DC Voltage measurement mode and return one reading    
    def read_dcv(self):
        self.write('FUNC "VOLT"')
        if self.notify:
            self.beep(1569.98, 0.05)
            self.beep(2093, 0.1)
        return self.read()
   
    # Set the device to AC Voltage measurement mode and return one reading
    def read_acv(self):
        self.write('FUNC "VOLT:AC"')
        return self.read()
    
    # Set the device to DC Current measurement mode and return one reading
    def read_dci(self):
        self.write('FUNC "CURR"')
        return self.read()
    
    # Set the device to AC Current measurement mode and return one reading
    def read_aci(self):
        self.write('FUNC "CURR:AC"')
        return self.read()
    
    # Read function type
    def read_func(self):
        return self.query('FUNC?').strip('\n')
    
    # Write function type
    def write_func(self, val):
        valid_vals = ['VOLT:DC', 'VOLT:AC', 'CURR:DC', 'CURR:AC', 'RES', 'FRES', 'DIOD', 'CAP', 'TEMP', 'CONT', 'FREQ:VOLT', 'PER:VOLT', 'VOLT:DC:RAT', 'DIG:VOLT', 'DIG:CURR']
        if val in valid_vals:
            self.write('FUNC "' + val + '"')
        else:
            raise ValueError('The specified function is not in the list of options.')
    
    # Read averaging type. Note: command is determined by current function, so first request function
    def read_avgtype(self):
        func = self.read_func()
        return self.visa.query(func + ':AVER:TCON?').strip('\n')
    
    def write_avgtype(self, val):
        if val in ['MOV', 'REP']:
            func = self.read_func()
            resp = self.visa.write(func + ':AVER:TCON ' + val)
        else:
            raise ValueError('The averaging type should be "MOV" (moving) or "REP" (repeating).')
        
    def read_avgcount(self):
        func = self.read_func()
        return self.visa.query(func + ':AVER:COUN?').strip('\n')
    
    def write_avgcount(self, val):
        if int(val) >= 1 and int(val) <= 100:
            func = self.read_func()
            resp = self.visa.write(func + ':AVER:COUN ' + str(val))
        else:
            raise ValueError('The filter count should lie within 1 - 100.')
            
    def read_avgstate(self):
        func = self.read_func()
        return self.visa.query(func + ':AVER:STAT?').strip('\n')
    
    def write_avgstate(self, val):
        func = self.read_func()
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write(func + ':AVER:STAT ON')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write(func + ':AVER:STAT OFF')
        else:
            raise ValueError('This is not a valid state.')

    def read_avgnplc(self):
        func = self.read_func()
        if func in ['VOLT:DC', 'CURR:DC', 'RES', 'FRES', 'DIOD', 'TEMP', 'VOLT:DC:RAT']:
            return float(self.visa.query(func + ':NPLC?').strip('\n'))
        else:
            raise ValueError('The PLC commands are only valid for DC measurement types.')
    
    def write_avgnplc(self, val):
        if float(val) >= 0.01 and float(val) <= 10:
            func = self.read_func()
            if func in ['VOLT:DC', 'CURR:DC', 'RES', 'FRES', 'DIOD', 'TEMP', 'VOLT:DC:RAT']:
                resp = self.visa.write(func + ':NPLC ' + str(val))
            else:
                raise ValueError('The PLC commands are only valid for DC measurement types.')
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

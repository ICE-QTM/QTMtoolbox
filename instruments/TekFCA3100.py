# -*- coding: utf-8 -*-
"""
Module to interact with a Agilent33220A series waveform generator.
Uses pyVISA to communicate with the GPIB device.

Version 1.0 (2020-06-11)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa
import time
from scipy import stats

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Agilent 33220A series. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class TekFCA3100:
    type = 'TekFCA3100'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Agilent E8241A series
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if not 'FCA3100' in model:
            raise WrongInstrErr('Expected Tektronix FCA3100 series, got {}'.format(resp))
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
        
    def read_tint(self):
        # Read value without reprogramming the instrument settings
        resp = self.visa.query('READ?').strip('\n')
        return float(resp)

# Read instrument settings ----------------------------------------------------
    def read_inpcoup1(self):
        # Reads whether input coupling 1 is AC or DC
        resp = self.visa.query('INP1:COUP?')
        return resp.strip('\n')

    def read_inpcoup2(self):
        # Reads whether input coupling 1 is AC or DC
        resp = self.visa.query('INP2:COUP?')
        return resp.strip('\n')    
    
    def read_inpatt1(self):
        # Reads whether input attenuation 1 is 1 or 10
        resp = self.visa.query('INP1:ATT?')
        return float(resp.strip('\n'))

    def read_inpatt2(self):
        # Reads whether input attenuation 2 is 1 or 10
        resp = self.visa.query('INP2:ATT?')
        return float(resp.strip('\n'))
    
    def read_inpimp1(self):
        # Reads whether input impedance 1 is 50 or 1E6 [Ohm]
        resp = self.visa.query('INP1:IMP?')
        return float(resp.strip('\n'))

    def read_inpimp2(self):
        # Reads whether input impedance 2 is 50 or 1E6
        resp = self.visa.query('INP2:IMP?')
        return float(resp.strip('\n'))  
    
    def read_inplvl1(self):
        # Reads the input 1 trigger level [Volt] when in MAN mode
        resp = self.visa.query('INP1:LEV?')
        return float(resp.strip('\n'))

    def read_inplvl2(self):
        # Reads the input 2 trigger level [Volt] when in MAN mode
        resp = self.visa.query('INP2:LEV?')
        return float(resp.strip('\n'))   
    
    def read_inplvlrel1(self):
        # Reads the input 1 trigger level [%] when in AUTO mode
        resp = self.visa.query('INP1:LEV:REL?')
        return float(resp.strip('\n'))

    def read_inplvlrel2(self):
        # Reads the input 2 trigger level [%] when in AUTO mode
        resp = self.visa.query('INP2:LEV:REL?')
        return float(resp.strip('\n'))  
    
    def read_inpauto1(self):
        # Reads the input 1 trigger type which is AUTO or MAN
        resp = self.visa.query('INP1:LEV:AUTO?')
        return float(resp.strip('\n'))

    def read_inpauto2(self):
        # Reads the input 2 trigger type which is AUTO or MAN
        resp = self.visa.query('INP2:LEV:AUTO?')
        return float(resp.strip('\n')) 
    
    def read_inpslop1(self):
        # Reads the input 1 trigger slope type which is POS or NEG
        resp = self.visa.query('INP1:SLOP?')
        return resp.strip('\n')

    def read_inpslop2(self):
        # Reads the input 1 trigger slope type which is POS or NEG
        resp = self.visa.query('INP2:SLOP?')
        return resp.strip('\n')
    
    def status1(self):
        print(self.read_inpcoup1())
        print(self.read_inpatt1())
        print(self.read_inplvlrel1())
        print(self.read_inpimp1())
        print(self.read_inpauto1())
        print(self.read_inpslop1())
    
# Write instrument settings ---------------------------------------------------
    # Valid options: AC , DC
    def write_inpcoup1(self, val):
        self.visa.write('INP1:COUP ' + val)
        
    def write_inpcoup2(self, val):
        self.visa.write('INP2:COUP ' + val)
    
    # Valid options: 1, 10
    def write_inpatt1(self, val):
        self.visa.write('INP1:ATT ' + str(val))

    def write_inpatt2(self, val):
        self.visa.write('INP2:ATT ' + str(val))
    
    # Valid options: 50, 1E6
    def write_inpimp1(self, val):
        self.visa.write('INP1:IMP ' + str(val))

    def write_inpimp2(self, val):
        self.visa.write('INP2:IMP ' + str(val))
    
    # Valid options: decimal number between -5 and 5 V in steps of 2.5 mV (for attenuation 1x) or -50 V and 50 V in steps of 25 mV (10x attenuation)
    def write_inplvl1(self, val):
        self.visa.write('INP1:LEV ' + str(val))

    def write_inplvl2(self, val):
        self.visa.write('INP2:LEV ' + str(val))
    
    # Valid options: percentage between 0 and 100
    def write_inplvlrel1(self, val):
        self.visa.write('INP1:LEV:REL ' + str(val))

    def write_inplvlrel2(self, val):
        self.visa.write('INP2:LEV:REL ' + str(val))
    
    # Valid options: 1 or 0
    def write_inpauto1(self, val):
        self.visa.write('INP1:LEV:AUTO ' + str(val))

    def write_inpauto2(self, val):
        self.visa.write('INP2:LEV:AUTO ' + str(val))
    
    # Valid options: POS or NEG
    def write_inpslop1(self, val):
        self.visa.write('INP1:SLOP ' + val)

    def write_inpslop2(self, val):
        self.visa.write('INP2:SLOP ' + val)
        
    def write_conf(self, val):
        self.visa.write('CONF:' + val)
    
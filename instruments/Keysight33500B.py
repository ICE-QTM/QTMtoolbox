# -*- coding: utf-8 -*-
"""
Module to interact with a Keysight 33500B series waveform generator.
Uses pyVISA to communicate with the USB/GPIB device.

Version 1.3 (2023-05-24)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl
"""

import pyvisa as visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keysight 33500B series. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keysight33500B:
    type = 'Keysight 33500B'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Keysight 33500B series
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if not '335' in model:
            raise WrongInstrErr('Expected Keysight 33500B series, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def query(self, val):
        resp = self.visa.query(val).strip('\n')
        return resp

    def close(self):
        self.visa.close()

    def read_amp(self):
        resp = float(self.visa.query('SOUR:VOLT?'))
        return resp

    def write_amp(self, val):
        val = float(val)
        self.visa.write('SOUR:VOLT ' + str(val))

    def read_offset(self):
        resp = float(self.visa.query('SOUR:VOLT:OFFSET?'))
        return resp

    def write_offset(self, val):
        val = float(val)
        self.visa.write('SOUR:VOLT:OFFSET ' + str(val))

    def read_freq(self):
        resp = float(self.visa.query('SOUR:FREQ?'))
        return resp

    def write_freq(self, val):
        val = float(val)
        self.visa.write('SOUR:FREQ ' + str(val))

    def read_waveform(self):
        resp = self.visa.query('SOUR:FUNC?').strip('\n')
        return resp

    def write_waveform(self, val):
        val = val.upper()
        if val in ['SIN', 'SQU', 'PULS', 'RAMP']:
            self.visa.write('SOUR:FUNC ' + str(val) + '\n')
        else:
            print('Warning! Function type not recognised.')

    def read_dutycycle(self):
        # Only for square waves
        resp = float(self.visa.query('SOUR:FUNC:SQU:DCYC?'))
        return resp

    def write_dutycycle(self, val):
        # Only for square waves
        val = float(val)
        self.visa.write('SOUR:FUNC:SQU:DCYC ' + str(val))

    def read_symm(self):
        # Only for ramp waves
        resp = float(self.visa.query('SOUR:FUNC:RAMP:SYMM?'))
        return resp

    def write_symm(self, val):
        # Only for ramp waves
        val = float(val)
        self.visa.write('SOUR:FUNC:RAMP:SYMM ' + str(val))

    def read_output(self):
        resp = self.visa.query('OUTP?').strip('\n')
        return resp
    
    def write_pulsedutycycle(self, val):
        # Only for pulse waves. Value between 0 and 100
        val = float(val)
        if (val >= 0) and (val <= 100):
            self.visa.write('SOUR:FUNC:PULS:DCYC ' + str(val))
        else:
            raise ValueError('The duty cycle should be within 0 and 100 %.')
            
    def read_pulsedutycycle(self):
        # Only for pulse waves
        resp = float(self.visa.query('SOUR:FUNC:PULS:DCYC?'))
        return resp  

    def read_pulsetranslead(self): 
        # Read pulse leading transition time, in seocnds
        resp = float(self.visa.query('SOUR:FUNC:PULSE:TRAN:LEAD?'))
        return resp

    def read_pulsetranstrail(self): 
        # Read pulse trailing transition time, in seocnds
        resp = float(self.visa.query('SOUR:FUNC:PULSE:TRAN:TRA?'))
        return resp

    def write_pulsetranslead(self, val):
        # Set pulse leading transition time. Value should be between 8.4 ns and 1 us
        val = float(val)
        if (val >= 8.4E-9) and (val <= 1E-6):
            self.visa.write('SOUR:FUNC:PULS:TRAN:LEAD ' + str(val))
        else:
            raise ValueError('The transition time should be between 8.4 ns and 1 us.')

    def write_pulsetranstrail(self, val):
        # Set pulse trailing transition time. Value should be between 8.4 ns and 1 us
        val = float(val)
        if (val >= 8.4E-9) and (val <= 1E-6):
            self.visa.write('SOUR:FUNC:PULS:TRAN:TRA ' + str(val))
        else:
            raise ValueError('The transition time should be between 8.4 ns and 1 us.') 
            
    def read_pulsewidth(self): 
        # Read pulse width in seconds
        resp = float(self.visa.query('SOUR:FUNC:PULSE:WIDT?'))
        return resp   

    def write_pulsewidth(self, val):
        # Set pulse width in seconds. Value should be between 16 ns up to period (1/freq)
        val = float(val)
        if (val >= 16E-9) and (val <= 1/self.read_freq()):
            self.visa.write('SOUR:FUNC:PULS:WIDT ' + str(val))
        else:
            raise ValueError('The pulse width should be between 16 ns and 1/f.')  

    def read_load(self):
        resp = self.visa.query('OUTP:LOAD?').strip('\n')
        # Note that the device returns 9.9E+37 if the load is INF.
        return resp

    def write_load(self, val):
        if val == 'INF':
            self.visa.write('OUTP:LOAD INF')
        else:
            val = float(val)
            self.visa.write('OUTP:LOAD ' + str(val))

    def square(self, amp, offset, freq, dutycycle=50):
        self.write_waveform('SQU')
        self.write_amp(amp)
        self.write_offset(offset)
        self.write_freq(freq)
        self.write_dutycycle(dutycycle)

    def sine(self, amp, offset, freq):
        self.write_waveform('SIN')
        self.write_amp(amp)
        self.write_offset(offset)
        self.write_freq(freq)
        
    def ramp(self, amp, offset, freq, symm):
        self.write_waveform('RAMP')
        self.write_amp(amp)
        self.write_offset(offset)
        self.write_freq(freq)
        self.write_symm(symm)

    def write_output(self, val):
        if val in ['ON', 'on', 1]:
            self.visa.write('OUTP 1')
        if val in ['OFF', 'off', 0]:
            self.visa.write('OUTP 0')
            
    def read_phase(self):
        self.visa.write('UNIT:ANGL DEG')
        return float(self.query('SOUR:PHAS?'))

    def write_phase(self, val):
        # Set the phase of the waveform in degrees. Default zero, range = [-360, 360]
        if (val >= -360) and (val <= 360):
            self.visa.write('UNIT:ANGL DEG')
            self.visa.write('SOUR:PHAS ' + str(val))
        else:
            raise ValueError('The phase should be within -360 and 360 degrees.')

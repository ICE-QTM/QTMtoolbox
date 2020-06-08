# -*- coding: utf-8 -*-
"""
Module to interact with a Keysight 33500B series waveform generator.
Uses pyVISA to communicate with the USB/GPIB device.

Version 1.0 (2020-06-08)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa

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
        resp = float(self.visa.query('SOUR:FUNC:SQU:DCYC?'))
        return resp

    def write_dutycycle(self, val):
        val = float(val)
        self.visa.write('SOUR:FUNC:SQU:DCYC ' + str(val))

    def read_output(self):
        resp = self.visa.query('OUTP?').strip('\n')
        return resp
    
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

    def write_output(self, val):
        if val in ['ON', 'on', 1]:
            self.visa.write('OUTP 1')
        if val in ['OFF', 'off', 0]:
            self.visa.write('OUTP 0')

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

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Agilent 33220A series. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class AgilentE8241A:
    type = 'AgilentE8241A'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Agilent E8241A series
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if not '8241A' in model:
            raise WrongInstrErr('Expected Agilent E8241A series, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp
    
    def query(self, val):
        resp = self.visa.query(val).strip('\n')
        return resp

    def close(self):
        self.visa.close()

    def read_amp(self):
        resp = float(self.visa.query('POW:AMPL?'))
        return resp

    def write_amp(self, val):
        val = float(val)
        self.visa.write('POW:AMPL ' + str(val) + ' dBm')

    def read_freq(self):
        resp = float(self.visa.query('FREQ:CW?'))
        return resp

    def write_freq(self, val):
        val = float(val)
        self.visa.write('FREQ ' + str(val) + ' Hz')
        
    def read_output(self):
        resp = int(self.visa.query('OUTP?'))
        return resp
    
    def write_output(self, val):
        if val in ['ON', 'on', 1]:
            self.visa.write('OUTP 1')
        if val in ['OFF', 'off', 0]:
            self.visa.write('OUTP 0')
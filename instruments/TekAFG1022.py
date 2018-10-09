# -*- coding: utf-8 -*-
"""
Module to interact with a Tektronix AFG1022.
Uses pyVISA to communicate with the USB/GPIB device.

Version 1.0 (2018-10-09)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Tektronix AFG1022. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class TekAFG1022:
    type = 'Tektronix AFG1022'

    def __init__(self, USBaddr='0x0699::0x0353::1525453'):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('USB0::{}::INSTR'.format(USBaddr))
        # Check if device is really a Tektronix AFG1022
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != 'AFG1022':
            raise WrongInstrErr('Expected Tektronix AFG1022, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()

    def read_amp(self):
        resp = float(self.visa.query('SOUR1:VOLT?'))
        return resp

    def write_amp(self, val):
        val = float(val)
        self.visa.write('SOUR1:VOLT ' + str(val) + '\n')

    def read_dcv(self):
        resp = float(self.visa.query('SOUR1:VOLT:OFFSET?').replace('V', ''))
        return resp

    def write_dcv(self, val):
        val = float(val)
        self.visa.write('SOUR1:VOLT:OFFSET ' + str(val) + '\n')

    def read_freq(self):
        resp = float(self.visa.query('SOUR1:FREQ?'))
        return resp

    def write_freq(self, val):
        val = float(val)
        self.visa.write('SOUR1:FREQ ' + str(val) + '\n')

    def read_waveform(self):
        resp = self.visa.query('SOUR1:FUNC?').strip('\n')
        return resp

    def write_waveform(self, val):
        val = val.upper()
        if val in ['SIN', 'SQU', 'PULS', 'RAMP', 'PRN']:
            self.visa.write('SOUR1:FUNC ' + str(val) + '\n')
        else:
            print('Warning! Function type not recognised.')

    def read_output(self):
        resp = self.visa.query('OUTP1?').strip('\n')
        return resp

    def write_output(self, val):
        if val in ['ON', 'on', 1]:
            self.visa.write('OUTP1 ON\n')
        if val in ['OFF', 'off', 0]:
            self.visa.write('OUTP1 OFF\n')

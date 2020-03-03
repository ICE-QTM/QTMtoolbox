# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 2400 SourceMeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.1 (2020-03-03)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 2400 SourceMeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keithley2400:
    type = 'Keithley 2400 SourceMeter'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Keithley 2400
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model not in ['MODEL 2400', 'MODEL 2401']:
            raise WrongInstrErr('Expected Keithley 2400/2401, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()

    def read_dcv(self):
        resp = float(self.visa.query('SOUR:VOLT:LEV:IMM:AMPL?').strip('\n'))
        return resp

    def write_dcv(self, val):
        # Check if value in between +/-180 V
        fval = float(val)
        if abs(fval) > 180:
            print('Your setpoint is higher than the allowed +/- 180 V and will not be applied.')
        else:
            self.visa.write('SOUR:VOLT:LEV ' + str(val) + '\n')

    def read_dci(self):
        resp = float(self.visa.query('SOUR:CURR:LEV:IMM:AMPL?'))
        return resp

    def write_dci(self, val):
        self.visa.write('SOUR:CURR:LEV ' + str(val) + '\n')

    def read_i(self):
        resp = str(self.visa.query('READ?').strip('\n'))
        val = float(resp.split(',')[1])
        return val
        
    def write_Vrange(self, val):
        if val in ['MAX', 'max', 'maximum', '210']:
            self.visa.write('SOUR:VOLT:RANG MAX\n')
        if val in ['DEF', 'def', 'default,', '21']
            self.visa.write('SOUR:VOLT:RANG DEF\n')
        if val in ['MIN', 'min', 'minimum']:
            self.visa.write('SOUR:VOLT:RANG MIN\n')

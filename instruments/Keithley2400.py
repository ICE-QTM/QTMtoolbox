# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 2400 SourceMeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.5 (2024-10-18)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl
"""

import pyvisa as visa

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

    def query(self, val):
        resp = self.visa.query(val).strip('\n')
        return resp

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

    def read_v(self):
        resp = str(self.visa.query('READ?').strip('\n'))
        val = float(resp.split(',')[0])
        return val

    def write_Vrange(self, val):
        if val in ['MAX', 'max', 'maximum', '210']:
            self.visa.write('SOUR:VOLT:RANG MAX\n')
        if val in ['DEF', 'def', 'default,', '21']:
            self.visa.write('SOUR:VOLT:RANG DEF\n')
        if val in ['MIN', 'min', 'minimum']:
            self.visa.write('SOUR:VOLT:RANG MIN\n')
            
    def write_Irange(self, val):
        if val in ['MAX', 'max', 'maximum', '1.05']:
            self.visa.write('SOUR:CURR:RANG MAX\n')
        elif val in ['DEF', 'def', 'default,', '100E-6']:
            self.visa.write('SOUR:CURR:RANG DEF\n')
        elif val in ['MIN', 'min', 'minimum', '1E-6']:
            self.visa.write('SOUR:CURR:RANG MIN\n')
        else :
            self.visa.write('SOUR:CURR:RANG ' + str(val) + '\n')

    def read_output(self):
        resp = int(self.visa.query('OUTP?').strip('\n'))
        return resp

    def write_output(self, val):
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('OUTP 1\n')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('OUTP 0\n')
        else:
            print('This is not a valid argument for the Keithley Output command. Your command will be ignored.')

    def read_Vcomptrip(self):
        # When sourcing current, this returns 1 if the voltage is above the compliance limit and 0 otherwise.
        resp = int(self.visa.query('SENS:VOLT:PROT:TRIP?').strip('\n'))
        return resp
    
    def read_Icomptrip(self):
        resp = int(self.visa.query('SENS:CURR:PROT:TRIP?').strip('\n'))
        return resp

    def read_Vcomplevel(self):
        # When sourcing a current, read the setpoint of the voltage compliance
        resp = float(self.visa.query('SENS:VOLT:PROT:LEV?').strip('\n'))
        return resp

    def read_Icomplevel(self):
        # When sourcing a voltage, read the setpoint of the current compliance
        resp = float(self.visa.query('SENS:CURR:PROT:LEV?').strip('\n'))
        return resp

    def write_Vcomplevel(self, val):
        self.visa.write('SENS:VOLT:PROT:LEV ' + str(val) + '\n')

    def write_Icomplevel(self, val):
        self.visa.write('SENS:CURR:PROT:LEV ' + str(val) + '\n')

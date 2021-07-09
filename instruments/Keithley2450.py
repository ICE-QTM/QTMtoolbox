# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 2450 SourceMeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.1 (2020-06-23)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import pyvisa as visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 2450 SourceMeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keithley2450:
    type = 'Keithley 2450 SourceMeter'

    def __init__(self, GPIBaddr=None):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Keithley 2450
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model not in ['MODEL 2450']:
            raise WrongInstrErr('Expected Keithley 2450, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def write_user_display(self, text1, text2):
        self.visa.write('DISP:CLE\n')
        self.visa.write('DISP:USER1:TEXT "' + text1 + '"\n')
        self.visa.write('DISP:USER2:TEXT "' + text2 + '"\n')

    def close(self):
        self.visa.close()

    def query(self, val):
        resp = self.visa.query(val).strip('\n')
        return resp

    def write(self, val):
        self.visa.write(val)

    def read_dcv(self):
        resp = float(self.visa.query('SOUR:VOLT:LEV:IMM:AMPL?').strip('\n'))
        return resp

    def write_dcv(self, val):
        fval = float(val)
        self.visa.write('SOUR:VOLT:LEV ' + str(fval) + '\n')
        self.write_user_display('Usetp = ' + str(fval) + 'V', 'QTMToolbox - Source DC voltage')


    def read_dci(self):
        resp = float(self.visa.query('SOUR:CURR:LEV:IMM:AMPL?'))
        return resp

    def write_dci(self, val):
        self.visa.write('SOUR:CURR:LEV ' + str(val) + '\n')
        self.write_user_display('Isetp = ' + str(val) + 'A', 'QTMToolbox - Source DC current')

    def read_i(self):
        # Note: the read_v is the same! For a Keithley 2450, there is no distinction here!
        # The user is responsible for selecting the right Measure Function on the device.
        resp = str(self.visa.query('READ?').strip('\n'))
        val = float(resp)
        return val

    def read_v(self):
        # Note: the read_v is the same! For a Keithley 2450, there is no distinction here!
        # The user is responsible for selecting the right Measure Function on the device.
        resp = str(self.visa.query('READ?').strip('\n'))
        val = float(resp)
        return val

    def write_Vrange(self, val):
        if val in ['MAX', 'max', 'maximum', '210']:
            self.visa.write('SOUR:VOLT:RANG MAX\n')
        elif val in ['DEF', 'def', 'default,', '21']:
            self.visa.write('SOUR:VOLT:RANG DEF\n')
        elif val in ['MIN', 'min', 'minimum']:
            self.visa.write('SOUR:VOLT:RANG MIN\n')

        else:
            # Check if value is a number
            val = float(val)
            self.visa.write('SOUR:VOLT:RANG ' + str(val) + '\n')

        self.write_user_display('New voltage range!', 'QTMToolbox - Notification')

    def read_output(self):
        resp = int(self.visa.query('OUTP?').strip('\n'))
        return resp

    def write_output(self, val):
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('OUTP 1\n')
            self.write_user_display('Output ON', 'QTMToolbox - Notification')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('OUTP 0\n')
            self.write_user_display('Output OFF', 'QTMToolbox - Notification')
        else:
            print('This is not a valid argument for the Keithley Output command. Your command will be ignored.')

    def read_inttrip(self):
        resp = int(self.visa.query('OUTP:INT:TRIP?\n').strip('\n'))
        return resp

    def read_readback(self):
        resp = int(self.visa.query('SOUR:VOLT:READ:BACK?\n').strip('\n'))
        return resp

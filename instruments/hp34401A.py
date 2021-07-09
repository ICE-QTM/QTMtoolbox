# -*- coding: utf-8 -*-
"""
Module to interact with a HP 34401A Multimeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.1 (2021-02-03)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import pyvisa as visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a HP 34401A Multimeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class hp34401A:
    type = 'HP 34401A Multimeter'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Keithley 2000
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != '34401A':
            raise WrongInstrErr('Expected HP 34401A, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()

    def read_dcv(self):
        resp = float(self.visa.query('READ?'))
        return resp

    def query(self, val):
        resp = self.visa.query(val).strip('\n')
        return resp

    def read_dcInputImp(self):
        resp = int(self.visa.query('INP:IMP:AUTO?'))
        return resp

    def write_dcInputImp(self, val):
        self.visa.write('INP:IMP:AUTO ' + str(val))

    def read_dcv_fast(self):
        resp = float(self.visa.query('MEAS:VOLT:DC? DEF, Max')) # Chuan: using max resolution to get a fast measurement
        return resp

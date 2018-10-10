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
    is not a Tektronix TDS 3012C. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class TekTDS3012C:
    type = 'Tektronix TDS 3012C'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Tektronix AFG1022
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != 'TDS 3012C':
            raise WrongInstrErr('Expected Tektronix TDS 3012C, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()

    def read_meas1(self):
        resp = self.visa.query('MEASU:MEAS1:VAL?')
        resp = float(resp.split(' ')[1])
        return resp

    def read_meas2(self):
        resp = self.visa.query('MEASU:MEAS2:VAL?')
        resp = float(resp.split(' ')[1])
        return resp
    
    def read_meas3(self):
        resp = self.visa.query('MEASU:MEAS3:VAL?')
        resp = float(resp.split(' ')[1])
        return resp
    
    def read_meas4(self):
        resp = self.visa.query('MEASU:MEAS4:VAL?')
        resp = float(resp.split(' ')[1])
        return resp
# -*- coding: utf-8 -*-
"""
Module to interact with a LakeShore 332 Temperature Controller.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.0 (2018-08-24)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com

Settings for the LakeShore controller (use <Interface> front button,
then cycle through menu with <Enter>):
- Baud rate:    9600
- IEEE addr:    choose GPIB address
- IEEE term:    Cr Lf
"""

import visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a LakeShore 332 Temperature Controller. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Lake332:
    type = 'LakeShore 332 Temperature Controller'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Lakeshore 332
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model not in ['MODEL332S', 'MODEL331S']:
            raise WrongInstrErr('Expected LakeShore 332S, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()

    def read_temp(self):
        resp = float(self.visa.query('KRDG? A'))
        return resp

    def write_PID(self, P, I, D):
        data = str(P) + ',' + str(I) + ',' + str(D)
        self.visa.write('PID 1,' + data)

    def write_setp(self, setp):
        self.visa.write('SETP 1,' + str(setp))

    def write_range(self, val):
        if val in ['Off', 'off', 0]:
            self.visa.write('RANGE 0')
        if val in ['Low', 'low', 1]:
            self.visa.write('RANGE 1')
        if val in ['Medium', 'medium', 2]:
            self.visa.write('RANGE 2')
        if val in ['High', 'high', 3]:
            self.visa.write('RANGE 3')
            
    def heater_off(self):
        self.visa.write('RANGE 0')

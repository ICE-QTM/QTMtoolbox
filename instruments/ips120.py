# -*- coding: utf-8 -*-
"""
Module to interact with an Oxford IPS120-10 Magnet Controller.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.0 (2018-09-09)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a IPS120-10 Magnet Controller. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class ips120:
    type = 'Oxford IPS120-10 Magnet Controller'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # The magnet controller neads a specific read termination:
        self.visa.read_termination = '\r'
        # Check if device is really an Oxford IPS120-10 Magnet Controller
        resp = self.visa.query('V')
        model = resp.split(' ')[0]
        if model != 'IPS120-10':
            raise WrongInstrErr('Expected Oxford IPS120-10, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('V'))
        return resp

    def close(self):
        self.visa.close()

    def unlock(self):
        self.visa.query('C 3')

    def read_fvalue(self):
        resp = float(self.visa.query('R 7').strip('R+').replace('+','').strip('\n').strip('\r'))
        return resp

    def write_fvalue(self, val):
        fval = float(val)
        self.visa.query('J ' + str(fval))
        # This only sets the field, but does not actually tell the magnet to go there. Thus:
        self.visa.query('A 1')

    def write_gotozero(self):
        self.visa.query('A 2')

    def read_rate(self):
        resp = float(self.visa.query('R 9').strip('R+').replace('+','').strip('\n').strip('\r'))
        return resp

    def write_rate(self, val):
        fval = float(val)
        self.visa.query('T ' + str(fval))

    def hold(self):
        self.visa.query('A 0')
        
    def clamp(self):
        self.visa.query('A 4')

    def hON(self):
        self.visa.query('H 1')

    def hOFF(self):
        self.visa.query('H 0')

    def read_setp(self):
        resp = float(self.visa.query('R 8').strip('R+').replace('+','').strip('\n').strip('\r'))
        return resp

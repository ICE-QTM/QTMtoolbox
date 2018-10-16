# -*- coding: utf-8 -*-
"""
Module to interact with a Scientific Instruments 9700 Temperature Controller.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.0 (2018-10-16)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Scientific Instruments 9700 Temperature Controller. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Lake332:
    type = 'Scientific Instruments 9700 Temperature Controller'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Lakeshore 332
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != '9700':
            raise WrongInstrErr('Expected Scientific Instruments 9700, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()

    def read_tempA(self):
        resp = float(self.visa.query('TA?'))
        return resp
		
	def read_tempB(self):
	    resp = float(self.visa.query('TA?'))
        return resp
		
	def read_setp(self):
		resp = float(self.visa.query('SET?'))
		return resp
		
	def write_setp(self, val):
		val = float(val)
		self.visa.write('SET ' + str(val))



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

import pyvisa as visa

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

    def query(self, val):
        resp = self.visa.query(val)
        return resp

    def read_heater(self):
        resp = int(self.visa.query('X').split('H')[1][0])
        return resp

    def status(self):
        resp = self.visa.query('X')
        print('--------------------------------------------------------------')
        print('Oxford IPS120-10 Magnet Power Supply')

        # We digest the XmnAnCnHnMmnPmn string piece by piece
        if resp[1] == '0':
            print('  System status 1: normal')
        elif resp[1] == '1':
            print('  System status 1: quenched')
        elif resp[1] == '2':
            print('  System status 1: over heated')
        elif resp[1] == '4':
            print('  System status 1: warming up')
        elif resp[1] == '8':
            print('  System status 1: fault')

        if resp[2] == '0':
            print('  System status 2: normal')
        elif resp[2] == '1':
            print('  System status 2: on positive voltage limit')
        elif resp[2] == '2':
            print('  System status 2: on negative voltage limit')
        elif resp[2] == '4':
            print('  System status 2: outside negative current limit')
        elif resp[2] == '8':
            print('  System status 2: outside positive current limit')

        if resp[4] == '0':
            print('  Activity:        hold')
        elif resp[4] == '1':
            print('  Activity:        to set point')
        elif resp[4] == '2':
            print('  Activity:        to zero')
        elif resp[4] == '4':
            print('  Activity:        clamped')

        if resp[6] == '0':
            print('  Loc/rem status:  local & locked')
        elif resp[6] == '1':
            print('  Loc/rem status:  remote & locked')
        elif resp[6] == '2':
            print('  Loc/rem status:  local & unlocked')
        elif resp[6] == '3':
            print('  Loc/rem status:  remote & unlocked')
        elif resp[6] == '4':
            print('  Loc/rem status:  auto-run-down')
        elif resp[6] == '5':
            print('  Loc/rem status:  auto-run-down')
        elif resp[6] == '6':
            print('  Loc/rem status:  auto-run-down')
        elif resp[7] == '0':
            print('  Loc/rem status:  auto-run-down')

        if resp[8] == '0':
            print('  Switch heater:   off magnet at zero (switch closed)')
        elif resp[8] == '1':
            print('  Switch heater:   on (switch open)')
        elif resp[8] == '2':
            print('  Switch heater:   off magnet at field (switch closed)')
        elif resp[8] == '5':
            print('  Switch heater:   heater fault (heater is on but current is low)')
        elif resp[8] == '8':
            print('  Switch heater:   no switch fitted')

        if resp[10] == '0':
            print('  Display mode 1:  amps (magnet sweep: fast)')
        elif resp[10] == '1':
            print('  Display mode 1:  tesla (magnet sweep: fast)')
        elif resp[10] == '4':
            print('  Display mode 1:  amps (magnet sweep: slow)')
        elif resp[10] == '5':
            print('  Display mode 1:  tesla (magnet sweep: slow)')

        if resp[11] == '0':
            print('  Display mode 2:  at rest')
        elif resp[11] == '1':
            print('  Display mode 2:  sweeping')
        elif resp[11] == '2':
            print('  Display mode 2:  sweep limiting')
        elif resp[11] == '3':
            print('  Display mode 2:  sweeping & sweep limiting')

        print('--------------------------------------------------------------')

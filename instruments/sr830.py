# -*- coding: utf-8 -*-
"""
Module to interact with a Stanford Research 830 Lock-In Amplifier.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.1 (2018-09-09)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa
import time
import numpy as np

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 2400 SourceMeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class sr830:
    type = 'Stanford Research 830 Lock-In Amplifier'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        self.GPIBnum = GPIBaddr
        # Check if device is really a sr830 lock-in
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != 'SR830':
            raise WrongInstrErr('Expected sr830 Lock-In Amplifier, got {}'.format(resp))

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        self.visa.close()

    def read_x(self):
        resp = float(self.visa.query('OUTP?1').strip('\n').strip('\r'))
        return resp

    def read_y(self):
        resp = float(self.visa.query('OUTP?2').strip('\n').strip('\r'))
        return resp

    def read_r(self):
        resp = float(self.visa.query('OUTP?3').strip('\n').strip('\r'))
        return resp

    def read_theta(self):
        resp = float(self.visa.query('OUTP?4').strip('\n').strip('\r'))
        return resp

    def read_freq(self):
        resp = float(self.visa.query('FREQ?').strip('\n').strip('\r'))
        return resp

    def read_amp(self):
        resp = float(self.visa.query('SLVL?').strip('\n').strip('\r'))
        return resp

    def write_amp(self, val):
        fval = float(val)
        self.visa.write('SLVL ' + str(fval) + '\n')

    def write_freq(self, val):
        fval = float(val)
        self.visa.write('FREQ ' + str(fval) + '\n')

    def read_phase(self):
        resp = float(self.visa.query('PHAS?').strip('\n').strip('\r'))
        return resp

    def write_phase(self, val):
        fval = float(val)
        self.visa.write('PHAS ' + str(fval) + '\n')

    def read_sens(self):
        resp = int(self.visa.query('SENS?').strip('\n').strip('\r'))
        return resp

    def write_sens(self, val):
        ival = float(val)
        self.visa.write('SENS ' + str(ival) + '\n')

    def read_dac1(self):
        resp = float(self.visa.query('AUXV?1').strip('\n').strip('\r'))
        return resp

    def write_dac1(self, val):
        fval = float(val)
        self.visa.write('AUXV1, ' + str(fval) + '\n')

    def read_dac2(self):
        resp = float(self.visa.query('AUXV?2').strip('\n').strip('\r'))
        return resp

    def write_dac2(self, val):
        fval = float(val)
        self.visa.write('AUXV2, ' + str(fval) + '\n')

    def read_dac3(self):
        resp = float(self.visa.query('AUXV?3').strip('\n').strip('\r'))
        return resp

    def write_dac3(self, val):
        fval = float(val)
        self.visa.write('AUXV3, ' + str(fval) + '\n')

    def read_dac4(self):
        resp = float(self.visa.query('AUXV?4').strip('\n').strip('\r'))
        return resp

    def write_dac4(self, val):
        fval = float(val)
        self.visa.write('AUXV4, ' + str(fval) + '\n')

    def read_auto_x(self):
        # Get data. We use the R value here!
        rval = float(self.visa.query('OUTP?3').strip('\n').strip('\r'))
        cur_sens = int(self.visa.query('SENS?').strip('\n').strip('\r'))
        sens = np.array([2e-9, 5e-9, 1e-8, 2e-8, 5e-8, 1e-7, 2e-7, 5e-7, 1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2, 1e-1, 2e-1, 5e-1, 1])
        sens_val = sens[cur_sens]
        # Change sensitivity if necessary
        changed = 0
        while abs(rval) > 0.9*sens_val:
            changed = 1
            cur_sens += 1
            self.visa.write('SENS ' + str(cur_sens) + '\n')
            time.sleep(5) # System must stabilise again
            rval = float(self.visa.query('OUTP?3').strip('\n').strip('\r'))
            cur_sens = int(self.visa.query('SENS?').strip('\n').strip('\r'))
            sens_val = sens[cur_sens]
        while abs(rval) < 0.1*sens_val:
            changed = 1
            cur_sens -= 1
            self.visa.write('SENS ' + str(cur_sens) + '\n')
            time.sleep(5) # System must stabilise again
            rval = float(self.visa.query('OUTP?3').strip('\n').strip('\r'))
            cur_sens = int(self.visa.query('SENS?').strip('\n').strip('\r'))
            sens_val = sens[cur_sens]

        #Notify user
        if changed == 1:
            print(' <!> Changed lock-in (GPIB: ' + str(self.GPIBnum) + ') sensitivity to ' + str(sens_val) + ' V.')

        # Return x-value to user
        xval = float(self.visa.query('OUTP?1').strip('\n').strip('\r'))
        return xval

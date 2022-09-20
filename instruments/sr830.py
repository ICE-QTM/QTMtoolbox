# -*- coding: utf-8 -*-
"""
Module to interact with a Stanford Research 830 Lock-In Amplifier.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.2 (2022-09-20)
Daan Wielens - Researcher at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa
import time
import numpy as np
import bisect as bisect

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
        
    def query(self, val):
        resp = self.visa.query(val)
        return resp
    
    def write(self, val):
        self.visa.write(val)
        
    def ask(self):
        return self.visa.read()

    def read_x(self):
        resp = float(self.query('OUTP?1').strip('\n').strip('\r'))
        return resp

    def read_y(self):
        resp = float(self.query('OUTP?2').strip('\n').strip('\r'))
        return resp

    def read_r(self):
        resp = float(self.query('OUTP?3').strip('\n').strip('\r'))
        return resp

    def read_theta(self):
        resp = float(self.query('OUTP?4').strip('\n').strip('\r'))
        return resp

    def read_freq(self):
        resp = float(self.query('FREQ?').strip('\n').strip('\r'))
        return resp

    def read_amp(self):
        resp = float(self.query('SLVL?').strip('\n').strip('\r'))
        return resp

    def write_amp(self, val):
        fval = float(val)
        self.write('SLVL ' + str(fval) + '\n')

    def write_freq(self, val):
        fval = float(val)
        self.write('FREQ ' + str(fval) + '\n')

    def read_phase(self):
        resp = float(self.query('PHAS?').strip('\n').strip('\r'))
        return resp

    def write_phase(self, val):
        fval = float(val)
        self.write('PHAS ' + str(fval) + '\n')

    def read_sens(self):
        resp = int(self.query('SENS?').strip('\n').strip('\r'))
        return resp

    def write_sens(self, val):
        ival = float(val)
        self.write('SENS ' + str(ival) + '\n')
    
    def read_time_const(self):
        resp = int(self.query('OFLT?').strip('\n').strip('\r'))
        return resp
    
    def write_time_const(self, val):
        ival = float(val)
        self.write('OFLT ' + str(ival) + '\n')

    def read_dac1(self):
        resp = float(self.query('AUXV?1').strip('\n').strip('\r'))
        return resp

    def write_dac1(self, val):
        fval = float(val)
        self.write('AUXV1, ' + str(fval) + '\n')

    def read_dac2(self):
        resp = float(self.query('AUXV?2').strip('\n').strip('\r'))
        return resp

    def write_dac2(self, val):
        fval = float(val)
        self.write('AUXV2, ' + str(fval) + '\n')

    def read_dac3(self):
        resp = float(self.query('AUXV?3').strip('\n').strip('\r'))
        return resp

    def write_dac3(self, val):
        fval = float(val)
        self.visa.write('AUXV3, ' + str(fval) + '\n')

    def read_dac4(self):
        resp = float(self.query('AUXV?4').strip('\n').strip('\r'))
        return resp

    def write_dac4(self, val):
        fval = float(val)
        self.visa.write('AUXV4, ' + str(fval) + '\n')
        
    def read_coupl(self):
        resp = int(self.query('ICPL?').strip('\n').strip('\r'))
        return resp

    def write_coupl(self, val):
        fval = int(val)
        self.visa.write('ICPL ' + str(fval) + '\n')

    def read_auto_x(self):
        # Get data. We use the R value here!
        rval = float(self.query('OUTP?3').strip('\n').strip('\r'))
        cur_sens = int(self.query('SENS?').strip('\n').strip('\r'))
        sens = np.array([2e-9, 5e-9, 1e-8, 2e-8, 5e-8, 1e-7, 2e-7, 5e-7, 1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2, 1e-1, 2e-1, 5e-1, 1])
        sens_val = sens[cur_sens]
        # Change sensitivity if necessary
        changed = 0
        while abs(rval) > 0.9*sens_val:
            changed = 1
            cur_sens += 1
            self.write('SENS ' + str(cur_sens) + '\n')
            time.sleep(5) # System must stabilise again
            rval = float(self.query('OUTP?3').strip('\n').strip('\r'))
            cur_sens = int(self.query('SENS?').strip('\n').strip('\r'))
            sens_val = sens[cur_sens]
        while abs(rval) < 0.1*sens_val:
            changed = 1
            cur_sens -= 1
            self.write('SENS ' + str(cur_sens) + '\n')
            time.sleep(5) # System must stabilise again
            rval = float(self.query('OUTP?3').strip('\n').strip('\r'))
            cur_sens = int(self.query('SENS?').strip('\n').strip('\r'))
            sens_val = sens[cur_sens]

        #Notify user
        if changed == 1:
            print(' <!> Changed lock-in (GPIB: ' + str(self.GPIBnum) + ') sensitivity to ' + str(sens_val) + ' V.')

        # Return x-value to user
        xval = float(self.query('OUTP?1').strip('\n').strip('\r'))
        return xval

    def write_auto_tau(self):
        tau = np.array([10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3, 300e-3, 1, 3, 10, 30, 100, 300, 1e3, 3e3, 10e3, 30e3])
        cur_freq = self.read_freq()
        cur_tau_i = self.read_time_const()
        
        #Calculate desired time constant: as hard lower limit: average over 10 oscillations of signal
        tau_target = 10*1/cur_freq
        
        #Set time constant to closest desired value: first to equal or exceed desired value
              
        #Find correct index for tau            
        i_tau = bisect.bisect_right(tau, tau_target)
        if tau[i_tau - 1]== tau_target:
            i_tau = i_tau - 1          
        
        #Check if tau needs to be changed
        if i_tau != cur_tau_i:
            tau_val = tau[i_tau]
            self.write_time_const(i_tau)
            print(' <!> Changed lock-in (GPIB: ' + str(self.GPIBnum) + ') timescale to ' + str(tau_val) + ' s.')
            
    def read_x_autotau(self):
       self.write_auto_tau()
       tau = np.array([10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3, 300e-3, 1, 3, 10, 30, 100, 300, 1e3, 3e3, 10e3, 30e3])
       cur_tau = tau[self.read_time_const()]
       cur_freq = self.read_freq()
       #Signal needs to stabilise
       print('freq = ' + str(cur_freq) + ', tau = ' + str(cur_tau) + ', stabilising signal')
       time.sleep(5*cur_tau)
       xval = self.read_auto_x()
       return xval

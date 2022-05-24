# -*- coding: utf-8 -*-
"""
Module to interact with a Cryomagnetics 4G-100 magnet power supply.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.0 (2022-05-23)
Daan Wielens - PhD at ICE/QTM
University of Twente
d.h.wielens@utwente.nl
"""

import pyvisa as visa
import numpy as np

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Cryomagnetics 4G-100. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class CM4G100:
    type = 'Cryomagnetics 4G-100'
    
    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a 4G-100
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model != '4G':
            raise WrongInstrErr('Expected Keithley 2000, got {}'.format(resp))  
        # The power supply presents values either in current or field, depending
        # on the selected units. Hence, always make sure to know what units are selected.
        self.units = self.visa.query('UNITS?').strip('\n')
        if self.units == 'A':
            print('Note: the magnet is configured to report its magnetic field as a current [Ampere]. To switch to field, change the units.')
        elif self.units == 'G' or self.units == 'kG':
            print('Note: the magnet is configured to report its magnetic field as a field [Gauss, kGauss, Tesla]. To switch to current, change the units.')
        else:
            raise ValueError('The units seem to be wrong. Please verify that the power supply works properly.')
    
    def convert_units(self, resp):
        if self.units == 'A':
            return float(resp.strip('A\n')) # Always units [A]
        if self.units in ['G', 'kG']:
            resp = resp.strip('\n')
            # Units can be [G, kG, T]. Always convert to Tesla
            if 'kG' in resp:
                resp = float(resp[:-2])/10
            elif 'G' in resp:
                resp = float(resp[:-1])*1E4
            elif 'T' in resp:
                resp = float(resp[:-1])
        return resp
    
    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp
    
    def query(self, val):
        resp = str(self.visa.query(val))
        return resp
    
    def write(self, val):
        resp = str(self.visa.write(val + '\n'))
        return resp
    
    def close(self):
        self.visa.close()
        
    def read_field(self):
        resp = self.query('IMAG?')
        return self.convert_units(resp)
    
    def read_units(self):
        resp = self.query('UNITS?')
        return resp.strip('\n')
        
    def write_units(self, val):
        if val in ['A', 'G']:
            self.write('UNITS ' + val)
            self.units = val

    def read_heater(self):
        resp = self.query('PSHTR?').strip('\n')
        return int(resp)

    def write_heater(self, val):
        if val in ['ON', 'OFF']:
            self.write('PSHTR ' + val)
        else:
            raise ValueError('The command accepts "ON" or "OFF" as arguments.')
    
    def read_llim(self):
        resp = self.query('LLIM?')
        return self.convert_units(resp)
        
    def read_ulim(self):
        resp = self.query('ULIM?')
        return self.convert_units(resp) 
    
    def write_llim(self, val):
        if self.units == 'A':
            if np.abs(val) > 85.94:
                raise ValueError('The magnet current can not exceed 85.94 A.')
            else:
                self.write('LLIM ' + str(val))
        if self.units == 'G':
            # We assume that the user writes a field value in Tesla
            if np.abs(val) > 8:
                raise ValueError('The magnetic field can not exceed 8 T.')
            else:
                self.write('LLIM ' + str(val*10)) # Power supply expects field in kG when self.units == 'G'. 
    
    def write_ulim(self, val):
        if self.units == 'A':
            if np.abs(val) > 85.94:
                raise ValueError('The magnet current can not exceed 85.94 A.')
            else:
                self.write('ULIM ' + str(np.abs(val)))
        if self.units == 'G':
            # We assume that the user writes a field value in Tesla
            if np.abs(val) > 8:
                raise ValueError('The magnetic field can not exceed 8 T.')
            else:
                self.write('ULIM ' + str(np.abs(val)*10)) # Power supply expects field in kG when self.units == 'G'.     

    # We only use range 0 ( == Range 1 on PSU), so the <1> is omitted in funtion names.
    def read_range(self):
        resp = self.query('RANGE? 0')
        return float(resp.strip('A\n'))
    
    def read_rate(self):
        resp = self.query('RATE? 0').strip('\n') # Given in A/s
        # To be consistent with the code for other magnet power supplies, we report values in [A/s, T/s], depending on self.units
        if self.units == 'A':
            return float(resp) # A/s
        if self.units in ['G', 'kG']:
            return float(resp)*930/1E4 # 930 Gauss/A / 10000 Gauss/T --> T/s
        
    def write_rate(self, val):
        if self.units == 'A':
            # The given value should be in A/s
            if val > 0.0898:
                raise ValueError('The rate can not exceed 0.0898 A/s.')
            else:
                self.write('RATE 0 ' + str(val))
        if self.units in ['G', 'kG']:
            # The given value should be in T/s
            if val > 0.0083514:
                raise ValueError('The rate can not exceed 0.0083514 T/s')
            else:
                val_As = val * 1E4/930
                if val_As < 0.0898:
                    self.write('RATE 0 ' + str(val_As))
                else:
                    raise ValueError('The rate is too large. This should not be possible given the previous check in [T/s].')
    
    def read_sweep(self):
        resp = self.query('SWEEP?').strip('\n')
        return resp
        # Possible responses: 'Sweeping up', 
    
    def write_sweep(self, val):
        if val in ['UP', 'DOWN', 'PAUSE', 'ZERO']:
            self.write('SWEEP ' + val)
        else:
            raise ValueError('This command accepts "UP", "DOWN", "PAUSE" or "ZERO" as arguments.')
    
    # Just as with the other power supplies, write_fvalue takes care of: 1. set setpoint as limit, 2. let magnet sweep to setpoint
    # The user can still choose to supply either [A] or [G] units. For the former, use Amperes. For the latter, supply the setpoint in Tesla.    
    def write_fvalue(self, val):
        if np.sign(val) > 0:
            self.write_ulim(val)
            self.write_sweep('UP')
        if np.sign(val) < 0:
            self.write_llim(val)
            self.write_sweep('DOWN')
        if np.sign(val) == 0:
            self.write_sweep('ZERO')
    
    # This function merely exists because of the 'sweep' command which requires that every parameter has both a read_ and write_ option.        
    def read_fvalue(self):
        return self.read_field()
    

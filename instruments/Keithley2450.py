# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 2450 SourceMeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 2.1 (2022-12-12)
Daan Wielens - Researcher at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import pyvisa as visa
import time

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 2450 SourceMeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keithley2450:
    type = 'Keithley 2450 SourceMeter'

    def __init__(self, addr=None, type='GPIB'):
        rm = visa.ResourceManager()
        if type == 'GPIB':
            self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(addr))
        elif type == 'USB':
            self.visa = rm.open_resource(addr)
        else:
            raise ValueError('Currently, connections can only be made either via USB (provide full USB::<>::INSTR string) or GPIB (provide number only).')
        # Check if device is really a Keithley 2450
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model not in ['MODEL 2450']:
            raise WrongInstrErr('Expected Keithley 2450, got {}'.format(resp))
            
        # Get initial state of device
        self.source_func = self.read_sourcefunc()
        self.sense_func = self.read_sensefunc()

    def get_iden(self):
        resp = str(self.visa.query('*IDN?'))
        return resp

    def write_user_display(self, text1, text2):
        self.visa.write('DISP:CLE\n')
        self.visa.write('DISP:USER1:TEXT "' + text1 + '"\n')
        self.visa.write('DISP:USER2:TEXT "' + text2 + '"\n')
        
    def beep(self, frequency, duration):
        self.visa.write('SYST:BEEP ' + str(frequency) + ', ' + str(duration))
        time.sleep(duration + 0.02)

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
        if not self.source_func == 'VOLT':
            print('<!> Warning: the device was not sourcing a voltage before. If the output was on, it has been switched off by the SMU. In that case, see on-screen warning for more information.')
            self.visa.write('SOUR:FUNC VOLT')
            self.read_sourcefunc()
        self.visa.write('SOUR:VOLT:LEV ' + str(fval) + '\n')

    def read_dci(self):
        resp = float(self.visa.query('SOUR:CURR:LEV:IMM:AMPL?'))
        return resp

    def write_dci(self, val):
        if not self.source_func == 'CURR':
            print('<!> Warning: the device was not sourcing current before. If the output was on, it has been switched off by the SMU. In that case, see on-screen warning for more information.')
            self.visa.write('SOUR:FUNC CURR')
            self.read_sourcefunc()
        self.visa.write('SOUR:CURR:LEV ' + str(val) + '\n')

    def read_i(self):
        return float(self.visa.query('MEAS:CURR?').strip('\n'))

    def read_v(self):
        # Both MEAS:VOLT? and READ? take the same processing time, so no nead to use READ? for speed.
        return float(self.visa.query('MEAS:VOLT?').strip('\n'))
    
    def read_r(self):
        return float(self.visa.query('MEAS:RES?').strip('\n'))
    
    def read_sourcefunc(self):
        self.source_func = self.visa.query('SOUR:FUNC?').strip('\n').replace('"', '')
        return self.source_func
    
    def read_sensefunc(self):
        self.sense_func = self.visa.query('SENS:FUNC?').strip('\n').replace('"', '')
        return self.sense_func
    
    def write_sourcefunc(self, val):
        if val in ['VOLT', 'CURR']:
            self.write('SOUR:FUNC ' + val)
        else:
            raise ValueError('One can either provide VOLT or CURR as inputs')
            
    def write_sensefunc(self, val):
        if val in ['"VOLT"', '"CURR"', '"RES"']:
            self.write('SENS:FUNC ' + val) 
        else:
            raise ValueError('One can either provide VOLT, CURR or RES as inputs')

    def write_Vrange(self, val):
        # Sets the range in such a way that the given value can be sourced
        val = float(val)
        self.visa.write('SOUR:VOLT:RANG ' + str(val) + '\n')
        
    def write_Irange(self, val):
        # Sets the range in such a way that the given value can be sourced
        val = float(val)
        self.visa.write('SOUR:CURR:RANG ' + str(val) + '\n')

    def read_Vcompliance(self):
        # This is a VOLTAGE compliance belonging to a CURRENT source
        return float(self.query('SOUR:CURR:VLIM?').strip('\n'))

    def read_Icompliance(self):
        # This is a CURRENT compliance belonging to a VOLTAGE source
        return float(self.query('SOUR:VOLT:ILIM?').strip('\n'))

    def write_Vcompliance(self, val):
        # This is a VOLTAGE compliance belonging to a CURRENT source
        val = float(val)
        self.visa.write('SOUR:CURR:VLIM ' + str(val) + '\n')

    def write_Icompliance(self, val):
        # This is a CURRENT compliance belonging to a VOLTAGE source
        val = float(val)
        self.visa.write('SOUR:VOLT:ILIM ' + str(val) + '\n')

    def read_output(self):
        resp = int(self.visa.query('OUTP?').strip('\n'))
        return resp

    def write_output(self, val):
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('OUTP 1\n')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('OUTP 0\n')
        else:
            print('This is not a valid argument for the Keithley Output command. Your command will be ignored.')

    def read_inttrip(self):
        resp = int(self.visa.query('OUTP:INT:TRIP?\n').strip('\n'))
        return resp

    def read_readback(self):
        resp = int(self.visa.query('SOUR:VOLT:READ:BACK?\n').strip('\n'))
        return resp

    def write_readback(self, val):
        # Get current function
        func = self.query('SOUR:FUNC?')
        # Set readback on/off
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('SOUR:' + func + ':READ:BACK ON')
        if val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('SOUR:' + func + ':READ:BACK OFF')
    
    def read_avgnplc(self):
        if self.sense_func == 'VOLT:DC':
            return float(self.query('SENS:VOLT:NPLC?'))
        if self.sense_func == 'CURR:DC':
            return float(self.query('SENS:CURR:NPLC?'))
        
        
    def read_avgnpts(self):
        if self.sense_func == 'VOLT:DC':
            return float(self.query('SENS:VOLT:AVER:COUN?'))
        elif self.sense_func == 'CURR:DC':
            return float(self.query('SENS:CURR:AVER:COUN?'))
        
            
    def info(self):
        print('-----------------------------------------------------')
        print('Source mode        :          ' + str(self.read_sourcefunc()))
        if self.source_func == 'VOLT':
            print('Source range       :          ' + self.query('SOUR:VOLT:RANG?') + ' V')
            print('Source compliance  :          ' + str(self.read_Icompliance()) + ' A')
        if self.source_func == 'CURR':
            print('Source range       :          ' + self.query('SOUR:CURR:RANG?') + ' A')
            print('Source compliance  :          ' + str(self.read_Vcompliance()) + ' A')
        print('Compliance reached :          ' + str(self.read_inttrip()))         
        print('Source readback    :          ' + str(self.read_readback())) 
        print('-----------------------------------------------------')
        print('Measurement mode   :          ' + str(self.read_sensefunc()))
        print('nPLC averaging     :          ' + str(self.read_avgnplc()))
        print('-----------------------------------------------------')

        

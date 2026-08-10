# -*- coding: utf-8 -*-
"""
Module to interact with a Keithley 2400 SourceMeter.
Uses pyVISA to communicate with the GPIB device.
Assumes GPIB address is of the form GPIB0::<xx>::INSTR where
<xx> is the device address (number).

Version 1.6 (2026-08-10)
Daan Wielens - Researcher at ICE/QTM
University of Twente
"""

import pyvisa as visa

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Keithley 2400 SourceMeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class Keithley2400:
    type = 'Keithley 2400 SourceMeter'

    def __init__(self, GPIBaddr):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))
        # Check if device is really a Keithley 2400
        resp = self.visa.query('*IDN?')
        model = resp.split(',')[1]
        if model not in ['MODEL 2400', 'MODEL 2401']:
            raise WrongInstrErr('Expected Keithley 2400/2401, got {}'.format(resp))

    def get_iden(self) -> str:
        """
        Returns the device identifier string.
        
        Returns
        ------
        str
            The device identifier string as given by the device.
        """
        resp = str(self.visa.query('*IDN?'))
        return resp

    def close(self):
        """
        Closes the GPIB session with the device.
        """
        self.visa.close()

    def query(self, val: str) -> str:
        """
        Queries the command specified by 'val' and returns the response of the device.
        
        Parameters
        ----------
        val : str
            The command that will be sent to the device.
        
        Returns
        ------
        str
            The unfiltered response of the device (only stripped from '\n'). 
        """
        resp = self.visa.query(val).strip('\n')
        return resp

    def read_dcv(self) -> float:
        """
        Returns the applied dc voltage when the device is in source:voltage mode.
        
        Returns
        ------
        float [Volts]
            The dc voltage that is applied by the SMU.
        """
        resp = float(self.visa.query('SOUR:VOLT:LEV:IMM:AMPL?').strip('\n'))
        return resp

    def write_dcv(self, val: float):
        """
        Writes the SMU setpoint to 'val' when the device is in source:voltage mode.
        
        Parameters
        ----------
        val : float [Volts]
            The voltage setpoint for the SMU.
        
        """
        self.visa.write('SOUR:VOLT:LEV ' + str(val) + '\n')

    def read_dci(self) -> float:
        """
        Returns the applied dc current when the device is in source:current mode.
        
        Returns
        ------
        float [Amps]
            The dc current that is applied by the SMU.
        """
        resp = float(self.visa.query('SOUR:CURR:LEV:IMM:AMPL?'))
        return resp

    def write_dci(self, val: float):
        """
        Writes the SMU setpoint to 'val' when the device is in source:current mode.
        
        Parameters
        ----------
        val : float [Amps]
            The current setpoint for the SMU.
        
        """
        self.visa.write('SOUR:CURR:LEV ' + str(val) + '\n')

    def read_i(self) -> float:
        """
        Returns the measured dc current.
        
        Returns
        ------
        float [Amps]
            The dc current that is measured by the SMU.
        """
        resp = str(self.visa.query('READ?').strip('\n'))
        val = float(resp.split(',')[1])
        return val

    def read_v(self) -> float:
        """
        Returns the measured dc voltage.
        
        Returns
        ------
        float [Volts]
            The dc voltage that is measured by the SMU.
        """
        resp = str(self.visa.query('READ?').strip('\n'))
        val = float(resp.split(',')[0])
        return val

    def write_Vrange(self, val: str | float):
        """
        Writes the SMU voltage range to 'val' when the device is in source:voltage mode.
        
        Parameters
        ----------
        val : str | float
            If type is 'float', the range will be chosen such that 'val' in Volts can 
            be applied by the SMU.
            If type is 'str', the range can be minimum, maximum or default. These options
            can be provided in lower and upper case (i.e. MAX, max, maximum).
        
        """
        if val in ['MAX', 'max', 'maximum', '210']:
            self.visa.write('SOUR:VOLT:RANG MAX\n')
        elif val in ['DEF', 'def', 'default,', '21']:
            self.visa.write('SOUR:VOLT:RANG DEF\n')
        elif val in ['MIN', 'min', 'minimum']:
            self.visa.write('SOUR:VOLT:RANG MIN\n')
        else:
            self.visa.write('SOUR:VOLT:RANG ' + str(val) + '\n')
            
    def write_Irange(self, val: str | float):
        """
        Writes the SMU current range to 'val' when the device is in source:current mode.
        
        Parameters
        ----------
        val : str | float
            If type is 'float', the range will be chosen such that 'val' in Amps can 
            be applied by the SMU.
            If type is 'str', the range can be minimum, maximum or default. These options
            can be provided in lower and upper case (i.e. MAX, max, maximum).
        
        """
        if val in ['MAX', 'max', 'maximum', '1.05']:
            self.visa.write('SOUR:CURR:RANG MAX\n')
        elif val in ['DEF', 'def', 'default,', '100E-6']:
            self.visa.write('SOUR:CURR:RANG DEF\n')
        elif val in ['MIN', 'min', 'minimum', '1E-6']:
            self.visa.write('SOUR:CURR:RANG MIN\n')
        else :
            self.visa.write('SOUR:CURR:RANG ' + str(val) + '\n')

    def read_output(self) -> int:
        """
        Returns whether the SMU's output is ON or OFF (1 or 0).
        
        Returns
        ------
        int
            If the output is ON, the SMU returns 1. If OFF, it returns 0.
        """
        resp = int(self.visa.query('OUTP?').strip('\n'))
        return resp

    def write_output(self, val: str | int):
        """
        Sets the output of the SMU to either ON or OFF.
        
        Parameters
        ----------
        val : str | int
            If type is 'int', one can provide either 1 or 0.
            If type is 'str', one can provide options in caps / mixed / small (i.e. ON, On, on).
        
        """
        if val in [1, 'On', 'ON', 'on']:
            self.visa.write('OUTP 1\n')
        elif val in [0, 'Off', 'OFF', 'off']:
            self.visa.write('OUTP 0\n')
        else:
            print('This is not a valid argument for the Keithley Output command. Your command will be ignored.')

    def read_Vcomptrip(self) -> int:
        """
        Returns whether the SMU's output is at compliance or not (1 or 0).
        
        Returns
        ------
        int
            If the compliance is reached the SMU returns 1, otherwise it returns 0.
        """
        # When sourcing current, this returns 1 if the voltage is above the compliance limit and 0 otherwise.
        resp = int(self.visa.query('SENS:VOLT:PROT:TRIP?').strip('\n'))
        return resp
    
    def read_Icomptrip(self) -> int:
        """
        Returns whether the SMU's output is at compliance or not (1 or 0).
        
        Returns
        ------
        int
            If the compliance is reached the SMU returns 1, otherwise it returns 0.
        """
        resp = int(self.visa.query('SENS:CURR:PROT:TRIP?').strip('\n'))
        return resp

    def read_Vcomplevel(self) -> float:
        """
        Returns the compliance voltage when in source:current mode.
        
        Returns
        ------
        float
            The compliance setpoint in Volts.
        """
        # When sourcing a current, read the setpoint of the voltage compliance
        resp = float(self.visa.query('SENS:VOLT:PROT:LEV?').strip('\n'))
        return resp

    def read_Icomplevel(self) -> float:
        """
        Returns the compliance current when in source:voltage mode.
        
        Returns
        ------
        float
            The compliance setpoint in Amps.
        """
        # When sourcing a voltage, read the setpoint of the current compliance
        resp = float(self.visa.query('SENS:CURR:PROT:LEV?').strip('\n'))
        return resp

    def write_Vcomplevel(self, val):
        """
        Writes the SMU compliance voltage setpoint to 'val'.
        
        Parameters
        ----------
        val : float [Volts]
            The compliance voltage setpoint.
        
        """
        self.visa.write('SENS:VOLT:PROT:LEV ' + str(val) + '\n')

    def write_Icomplevel(self, val):
        """
        Writes the SMU compliance current setpoint to 'val'.
        
        Parameters
        ----------
        val : float [Amps]
            The compliance voltage setpoint.
        
        """
        self.visa.write('SENS:CURR:PROT:LEV ' + str(val) + '\n')

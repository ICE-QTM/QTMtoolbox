# -*- coding: utf-8 -*-
"""
Module to interact with a Thales PTR controller (XPCDE4865/X).
Uses a serial connection to communicate with the device.

Version 2.1 (2026-08-10)
Daan Wielens - Researcher at ICE/QTM
University of Twente

New in V2.0: updated temperature conversion to use polynomial fit on data instead of linear approximation.

<!> For other users / labs: please update the thermometry fitting parameters for your sensor!
"""

import serial
import numpy as np

# --- Thermometry conversion constants ---
'''
For the thermometry conversion we use 4th-order polynomials to fit T(V) and V(T)
Fit equation: y = a + b*x + c*x^2 + d*x^3 + e*x^4
'''
# Volts to Kelvin
aVK = 418.15618
bVK = 359.35795
cVK = -1743.62202
dVK = 1700.28623
eVK = -635.4725

# Kelvin to Volts
aKV = 1.14512
bKV = -0.00113
cKV = -3.91435E-6
dKV = 4.6483E-9
eKV = 8.22724E-15

class ThalesPTR:
    type = 'Thales PTR cooler'
    
    def mVtoK(self, Vsensor):
        x = Vsensor / 1e3 # Convert from mV to V
        Tsensor = aVK + bVK*x + cVK*x**2 + dVK*x**3 + eVK*x**4 
        return Tsensor

    def KtomV(self, temp):
        Vsensor = aKV + bKV*temp + cKV*temp**2 + dKV*temp**3 + eKV*temp**4
        return Vsensor * 1e3 # Convert from V to mV
    
    def __init__(self, COMport=3):
        self.ser = serial.Serial()
        self.ser.baudrate = 9600
        self.ser.port = 'COM' + str(COMport)
        self.ser.stopbits = 1
        self.ser.bytesize = 8
        self.ser.timeout = 1
        
    def query(self, val):
        self.ser.open()
        self.ser.write((val + '\r').encode())
        resp = self.ser.readline().decode().strip('\r\n')
        self.ser.close()
        return resp
    
    def write(self, val):
        self.ser.open()
        self.ser.write((val + '\r').encode())
        self.ser.readline().decode() # The device always gives a reply, so always catch it.
        self.ser.close()

    def read_Vsetp(self) -> float:
        """
        Returns the voltage setpoint of the temperature controller.
        
        Returns
        ------
        float [mV]
            The voltage setpoint of the temperature controller.
        """
        return float(self.query('RSP'))
    
    def read_Vsensor(self) -> float:
        """
        Returns the actual voltage of the temperature sensor.
        
        Returns
        ------
        float [mV]
            The actual voltage of the temperature sensor.
        """
        return float(self.query('RVS'))
    
    def read_Vac(self) -> float:
        """
        Returns the RMS drive voltage that is applied to the compressor.
        
        Returns
        ------
        float [Volts]
            The RMS drive voltage that is applied to the compressor.
        """
        return float(self.query('RVA'))
    
    def read_Vdc(self) -> float:
        """
        Returns the actual DC supply voltage of the controller.
        
        Returns
        ------
        float [Volts]
            The DC supply voltage.
        """
        return float(self.query('RVD'))
    
    def read_freq(self) -> float:
        """
        Returns the frequency at which the cooler is driven.
        
        Returns
        ------
        float [Hz]
            The frequency at which the cooler is driven.
        """
        return float(self.query('RFR'))
    
    def read_remote(self) -> int:
        """
        Returns the status of the remote on/off function.
        
        Returns
        ------
        int
            1: Remote status = on
            0: Remote status = off
        """
        return int(self.query('RRE'))
    
    def read_temp(self) -> float:
        """
        Returns the temperature of the cold head. This temperature is 
        based on the thermometer voltage which is converted based on 
        calibration data.
        
        Returns
        ------
        float [K]
            The cold head temperature.
        """
        return self.mVtoK(self.read_Vsensor())
    
    def read_Tsetp(self) -> float:
        """
        Returns the temperature setpoint of the cooler. This temperature is 
        based on the thermometer voltage which is converted based on 
        calibration data.
        
        Returns
        ------
        float [K]
            The temperature setpoint of the cooler.
        """
        return self.mVtoK(self.read_Vsetp())
    
    def write_Vsetp(self, val: float):
        """
        Writes the voltage setpoint for the temperature controller. 
        
        Parameters
        ----------
        val : float [mV] 
            The voltage setpoint for the temperature controller.
            Note that 0.2 <= val <= 5000 
        """
        if val >= 0.2 and val <= 5000:
            self.write('SSP ' + str(np.round(val, 3)))
        else:
            raise ValueError('Voltage setpoint [mV] needs to be within 0.2 and 5000 mV')
            
    def write_remote(self, val: int):
        """
        Sets the remote function of the cooler on or off. 
        
        Parameters
        ----------
        val : int
            1: Remote status = on
            0: Remote status = off
        """
        if val == 0 or val == 1:
            self.write('SRE ' + str(val))
            
    def write_Tsetp(self, val: float):
        """
        Writes the temperature setpoint for the controller. This temperature is 
        based on the thermometer voltage which is converted based on 
        calibration data.
        
        Parameters
        ----------
        val : float [K] 
            The temperature setpoint for the controller.
            Note that 50 <= val <= 300
        """
        # This check ensures that the temperatures are within the allowed range
        if val >= 50 and val <= 300:
            # This furthermore will ensure that the voltage setpoint is within range of the controller 
            self.write_Vsetp(self.KtomV(val))
        else:
            raise ValueError('Temperature setpoint [K] needs to be within 50 and 300 K.')
        

# -*- coding: utf-8 -*-
"""
Module to interact with a Delft IVVI DAC module.
Uses the pySerial module to communicate with the device.
Assumes the address is of the form COM<xx> where
<xx> is the relevant port.

We assume that the IVVI rack has 16 DACs.
Script based on: http://qtwork.tudelft.nl/~schouten/ivvi/doc-d5/rs232linkformat.txt

Version 1.2 (2019-08-29)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import serial

class IVVI:
    type = 'Delft IVVI DAC module'

    def __init__(self, COMport):
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.port = 'COM' + str(COMport)
        self.ser.parity = serial.PARITY_ODD
        self.ser.stopbits = 1
        self.ser.bytesize = 8
        try:
            self.ser.open()
        except Exception:
            print('Serial port to IVVI rack is already open. Skipping initialisation.')

    def close(self):
        self.ser.close()

    def read_dacs(self):
        read_msg = bytes([4, 0, 34, 2])
        self.ser.write(read_msg)
        resp = self.ser.read(34)

        values_int = list(range(16))
        values_Volts = list(range(16))
        for i in range(16):
            values_int[i] = int.from_bytes(resp[2*(i+1):4+2*i], byteorder='big')
            values_Volts[i] = round(((values_int[i]) / 65535 * 4 - 2), 8)

        return values_Volts
    
    def write_dac(self, dac, val):
        val = float(val)
        dac = int(dac)
        
        # Range checks
        if val > 2:
            print('DAC1 setpoint > 2. The setpoint will be set to 2.')
            val = 2
        elif val < -2:
            print('DAC1 setpoint < -2. The setpoint will be set to -2.')
            val = -2    
        
        # Change setpoint
        bytevalue = int(((val+2)/4) * 65535).to_bytes(length=2, byteorder='big') 
        set_msg = bytes([7, 0, 2, 1, dac]) + bytevalue
        self.ser.write(set_msg)
        self.ser.read(2)
        
    def read_dac(self, dac):
        if (dac > 0) and (dac < 17):
            resp = self.read_dacs()
            resp = resp[dac-1]
            return resp
        else:
            raise ValueError('The <dac> integer must be within 1-16')

    def read_dac1(self):
        resp = self.read_dacs()
        resp = resp[0]
        return resp

    def write_dac1(self, val):
        self.write_dac(1, val)
        
    def read_dac2(self):
        resp = self.read_dacs()
        resp = resp[1]
        return resp

    def write_dac2(self, val):
        self.write_dac(2, val)
        
    def read_dac3(self):
        resp = self.read_dacs()
        resp = resp[2]
        return resp

    def write_dac3(self, val):
        self.write_dac(3, val)
        
    def read_dac4(self):
        resp = self.read_dacs()
        resp = resp[3]
        return resp

    def write_dac4(self, val):
        self.write_dac(4, val)
        
    def write_dacszero(self):
        for i in range(16):
            self.write_dac(i+1, 0)


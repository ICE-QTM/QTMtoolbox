# -*- coding: utf-8 -*-
"""
Module to interact with a Delft IVVI DAC module.
Uses the pySerial module to communicate with the device.
Assumes the address is of the form COM<xx> where
<xx> is the relevant port.

We assume that the IVVI rack has 16 DACs.
Script based on: http://qtwork.tudelft.nl/~schouten/ivvi/doc-d5/rs232linkformat.txt

The serial connection is opened/closed after every command. This increases
the stability of the dac and reduces the chance to setup multiple connections
to the device.

Version 2.2 (2022-10-28)
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

    def read_dacs(self):
        read_msg = bytes([4, 0, 34, 2])
        self.ser.open()
        self.ser.write(read_msg)
        resp = self.ser.read(34)
        self.ser.close()

        values_int = list(range(16))
        values_Volts = list(range(16))
        for i in range(16):
            values_int[i] = int.from_bytes(resp[2*(i+1):4+2*i], byteorder='big')
            values_Volts[i] = round(((values_int[i]) / 65535 * 4 - 2), 8)

        return values_Volts, values_int
    
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
        self.ser.open()
        self.ser.write(set_msg)
        self.ser.read(2)
        self.ser.close()
        
    def read_dac(self, dac):
        if (dac > 0) and (dac < 17):
            resp = self.read_dacs()[0]
            resp = resp[dac-1]
            return resp
        else:
            raise ValueError('The <dac> integer must be within 1-16')
            
    def read_dac_byte(self, dac):
        if (dac > 0) and (dac < 17):
            resp = self.read_dacs()[1]
            resp = resp[dac-1]
            return resp
        else:
            raise ValueError('The <dac> integer must be within 1-16')

    # Create functions for reading any DAC channel (chan. 1-16) in the system
    for i in range(16):
        exec("def read_dac" + str(i+1) + "(self):\n" +
             "    return(self.read_dac(" + str(i+1) + "))")
        
    # Create functions for reading any DAC channel (chan. 1-16) as byte values
    for i in range(16):
        exec("def read_dac_byte" + str(i+1) + "(self):\n" + 
             "    return(self.read_dac_byte(" + str(i+1) + "))")

    # Create functions for setting any DAC channel (chan. 1-16) in the system
    for i in range(16):
        exec("def write_dac" + str(i+1) + "(self, val):\n" +
             "    self.write_dac(" + str(i+1) + ", str(val))")
        
    def write_dacszero(self):
        for i in range(16):
            self.write_dac(i+1, 0)

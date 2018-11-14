# -*- coding: utf-8 -*-
"""
Module to interact with a Delft IVVI DAC module.
Uses the pySerial module to communicate with the device.
Assumes the address is of the form COM<xx> where
<xx> is the relevant port.

Version 1.0 (2018-11-14)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import serial

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a Delft IVVI DAC module. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

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

    def read_dac1(self):
        resp = self.read_dacs()
        resp = resp[0]
        return resp

    # def write_dac1(self, val):
    #     # Does not work yet!!
    #     val = float(val)
    #     bytevalue = int((val+2)/65535).to_bytes(length=2, byteorder='big')
    #     set_msg = bytes([7, 0, 2, 1, 1]) + bytevalue
    #     self.ser.write(set_msg)
    #     self.ser.read(2)

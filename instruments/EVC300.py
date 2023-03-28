# -*- coding: utf-8 -*-
"""
Module to interact with a Focus EVC300 module.
Uses the pySerial module to communicate with the device.
Assumes the address is of the form COM<xx> where
<xx> is the relevant port.

Version 1.0 (2023-02-27)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl
"""

import serial

class EVC300:
    type = 'Focus EVC300'

    def __init__(self, COMport):
        self.ser = serial.Serial()
        self.ser.baudrate = 57600
        self.ser.port = 'COM' + str(COMport)
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = 1
        self.ser.bytesize = 8
        self.ser.xonxoff = True
        self.ser.timeout = 3
    
    def read_HV(self):
        # Retrieve the high voltage (V)
        self.ser.open()
        self.ser.write('GET HV\r\n'.encode())
        resp = self.ser.read_until().decode()
        self.ser.close() 
        return float(resp.strip('\r\n'))
    
    def write_HV(self, val):
        # Set the high voltage (V). If a + or - is put before the value, the value is interpreted as increment and not absolute setpoint.
        self.ser.open()
        self.ser.write(('SET HV ' + str(val) + '\r').encode())
        self.ser.close()
        
    def read_emis(self):
        # Read the emission current (mA)
        self.ser.open()
        self.ser.write('GET EMIS\r\n'.encode())
        resp = self.ser.read_until().decode()
        self.ser.close() 
        return float(resp.strip('\r\n'))
    
    def write_emis(self, val):
        # Write the emission current (mA)
        self.ser.open()
        self.ser.write(('SET EMIS ' + str(val) + '\r').encode())
        self.ser.close()
        
    def read_fil(self):
        # Read the filament current (A)
        self.ser.open()
        self.ser.write('GET FIL\r\n'.encode())
        resp = self.ser.read_until().decode()
        self.ser.close() 
        return float(resp.strip('\r\n'))        

    def write_fil(self, val):
        # Write the filament current (A)
        self.ser.open()
        self.ser.write(('SET FIL ' + str(val) + '\r').encode())
        self.ser.close()
        
    def read_flux(self):
        # Read the flux (A)
        self.ser.open()
        self.ser.write('GET FLUX\r\n'.encode())
        resp = self.ser.read_until().decode()
        self.ser.close() 
        return float(resp.strip('\r\n')) 

    def read_shutter(self):        
        # Read the shutter position
        self.ser.open()
        self.ser.write('GET SHUTTER\r\n'.encode())
        resp = self.ser.read_until().decode().strip('\r\n')
        self.ser.close() 
        if resp == 'CELL CLOSED':
            return 0
        if resp == 'CELL OPEN':
            return 1
    
    def read_emiscontrol(self):
        # Read whether the system is in emission control (0 = emis, 1 = fil)
        self.ser.open()
        self.ser.write('GET EMISCON\r\n'.encode())
        resp = self.ser.read_until().decode()
        self.ser.close()
        return int(resp.strip('\r\n'))
    
    def read_automodus(self):
        # Read whether the system is in flux regulation mode (0 = off, 1 = on)
        self.ser.open()
        self.ser.write('GET AUTOMODUS\r\n'.encode())
        resp = self.ser.read_until().decode()
        self.ser.close()
        return int(resp.strip('\r\n'))  
    
    def read_temp(self):
        # Read cooling shroud temperature (degC)
        self.ser.open()
        self.ser.write('GET TEMP\r\n'.encode())
        resp = self.ser.read_until().decode()
        self.ser.close() 
        return float(resp.strip('\r\n'))
    
    def info(self):
        print('-----------------------------------------------')
        print('Filament current   :        ' + str(self.read_fil()) + ' A')
        print('Emisison current   :        ' + str(self.read_fil()) + ' mA')
        print('High voltage       :        ' + str(self.read_HV()) + ' V')
        print('Emission control   :        ' + str(self.read_emiscontrol()))
        print('Flux regulation    :        ' + str(self.read_automodus()))
        print('Shroud temperature :        ' + str(self.read_temp()) + ' degC')
        print('Shutter            :        ' + str(self.read_shutter()))
        print('-----------------------------------------------')
        
        
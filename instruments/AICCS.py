# -*- coding: utf-8 -*-
"""
Module to interact with the AI-CCS.
Uses TCP/IP sockets to communicate with the device.

Version 1.1 (2026-09-04)
Daan Wielens - Researcher at ICE/QTM
University of Twente
"""

import socket

class AICCS:
    type = 'AICCS'

    def __init__(self, IPaddress, port=5025):
        # Port should be a number, not a string
        if not isinstance(port, int):
            port = int(port)
        # Prepare socket instance
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.connect((IPaddress, port))

    def close(self):
        self.s.close()
        
    def query(self, val):
        cmd = val + '\n'
        self.s.sendall(cmd.encode())
        resp = self.s.recv(1400).decode()
        return resp
    
    def write(self, val):
        cmd = val + '\n'
        self.s.sendall(cmd.encode())

    def get_iden(self):
        self.s.sendall('*IDN?\n'.encode())
        resp = self.s.recv(1400).decode()
        return resp
   
    # The supported current range is +- 4mA.  
    # On a pair, currents must have opposite sign. When setting a channels current to a value that 
    # will change the channels polarity, the other channel in the pair will be set to 0.0mA.   
    def write_dci1A(self, val):
        self.write('SOUR1A ' + str(val))
        
    def write_dci1B(self, val):
        self.write('SOUR1B ' + str(val))
        
    def write_dci2A(self, val):
        self.write('SOUR2A ' + str(val))
        
    def write_dci2B(self, val):
        self.write('SOUR2B ' + str(val))
        
    def read_dci1A(self):
        return float(self.query('SOUR1A:CURR?'))

    def read_dci1B(self):
        return float(self.query('SOUR1B:CURR?'))

    def read_dci2A(self):
        return float(self.query('SOUR2A:CURR?'))

    def read_dci2B(self):
        return float(self.query('SOUR2B:CURR?'))  

    def read_v1A(self):
        return float(self.query('MEAS1A?'))

    def read_v1B(self):
        return float(self.query('MEAS1B?'))
    
    def read_v2A(self):
        return float(self.query('MEAS2A?'))
    
    def read_v2B(self):
        return float(self.query('MEAS2B?'))
    
    # Output can be 0 (OFF), 1 (ON) or 2 (SHUNT)
    def write_output1(self, val):
        self.write('OUTP1A ' + str(val))
        
    def write_output2(self, val):
        self.write('OUTP2A ' + str(val))
        
    def read_output1(self):
        return int(self.query('OUTP1A?'))
    
    def read_output2(self):
        return int(self.query('OUTP2A?'))
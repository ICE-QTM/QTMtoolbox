# -*- coding: utf-8 -*-
"""
Module to interact with an Rohde & Schwarz Vector Network Analyzer.
Uses sockets to communicate with the ethernet device.

Version 1.0 (2025-10-23)
Daan Wielens - Researcher at ICE/QTM
University of Twente
"""

import socket
import numpy as np

class ZNLE18:
    type = 'RohdeSchwarzZNL18'
    
    def __init__(self, IPaddress='169.254.196.64'):
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.connect((IPaddress, 5025))
        
    def close(self):
        self.s.close()
        
    def query(self, val):
        cmd = val + '\r\n'
        self.s.sendall(cmd.encode())
        resp = self.s.recv(2048).decode()
        return resp    
    
    def write(self, val):
        cmd = val + '\r\n'
        self.s.sendall(cmd.encode())
        
    
    def get_iden(self):
        self.s.sendall('*IDN?\r\n'.encode())
        resp = self.s.recv(2048).decode()
        return resp
    
    # Read and write frequencies (all in Hz)
    def read_fstart(self):
        return float(self.query('SENS:FREQ:STAR?'))
    
    def read_fstop(self):
        return float(self.query('SENS:FREQ:STOP?'))
    
    def read_fcent(self):
        return float(self.query('SENS:FREQ:CENT?'))
    
    def read_fspan(self):
        return float(self.query('SENS:FREQ:SPAN?'))
        
    def write_fstart(self, val):
        self.write('SENS:FREQ:STAR ' + str(val))
        
    def write_fstop(self, val):
        self.write('SENS:FREQ:STOP ' + str(val))
        
    def write_fcent(self, val):
        self.write('SENS:FREQ:CENT ' + str(val))
        
    def write_fspan(self, val):
        self.write('SENS:FREQ:SPAN ' + str(val))
                
    # Read and write number of points
    def read_npoints(self):
        return int(self.query('SENS1:SWE:POIN?'))
    
    def write_npoints(self, val):
        self.write('SWE:POIN ' + str(val))
    
    # Return sweep time in seconds
    def read_sweeptime(self):
        return float(self.query('SENS1:SWE:TIME?'))
    
    def read_data1(self):
        data = self.query('CALC:DATA? FDAT')
        # Keep requesting data from buffer until finished by '\n' character
        while '\n' not in data:
            data = data + self.s.recv(2048).decode()
        ldata = np.array(data.split(','), dtype='float')
        return ldata
    
    def read_xdata(self):
        data = self.query('CALC:DATA:STIM?')
        # Keep requesting data from buffer until finished by '\n' character
        while '\n' not in data:
            data = data + self.s.recv(2048).decode()
        ldata = np.array(data.split(','), dtype='float')
        return ldata
        
    # Source power
    def read_sourcepower(self):
        return float(self.query('SOUR1:POW?'))
    
    def write_sourcepower(self, val):
        self.write('SOUR1:POW ' + str(val))
        
    # Read trace
    def get_trace1(self):
        # The device gives more data than nbytes indicates, so lets check against npoints
        npoints = self.read_npoints()
        # The command send two responses: firstly the header indicating the block length (which we ignore), then the data itself
        resp = self.query('TRAC:DATA? 1')
        nbytes = int(resp[2:])
        # Keep receiving data until we got it all (based on length of splitted string)
        commas = 0 
        data = ''
        while commas < npoints - 1:
            resp = self.s.recv(nbytes).decode()
            data = data + resp          
            commas = len(data.split(','))
        # The data is now a string of '-169.22', '-140.22', ... , so convert to float array  

        return np.array(data.split(','), dtype=np.float32)

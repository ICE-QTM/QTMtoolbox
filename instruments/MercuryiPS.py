# -*- coding: utf-8 -*-
"""
Module to interact with the Oxford MercuryiPS.
Uses TCP/IP sockets to communicate with the device.

Version 1.0 (2018-12-05)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import socket

class MercuryiPS:
    type = 'MercuryiPS'

    def __init__(self, IPaddress, port=7020):
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
        cmd = val + '\r\n'
        self.s.sendall(cmd.encode())
        resp = self.s.recv(1400).decode()
        return resp

    def get_iden(self):
        self.s.sendall('*IDN?\r\n'.encode())
        resp = self.s.recv(1400).decode()
        return resp
    
    def read_fvalueX(self):
        self.s.sendall('READ:DEV:GRPX:PSU:SIG:FLD\r\n'.encode())
        resp = self.s.recv(1400).decode()
        resp = float(resp.split(':')[-1].strip('T\n'))
        return resp
    
    def read_fvalueY(self):
        self.s.sendall('READ:DEV:GRPY:PSU:SIG:FLD\r\n'.encode())
        resp = self.s.recv(1400).decode()
        resp = float(resp.split(':')[-1].strip('T\n'))
        return resp

    def read_fvalueZ(self):
        self.s.sendall('READ:DEV:GRPZ:PSU:SIG:FLD\r\n'.encode())
        resp = self.s.recv(1400).decode()
        resp = float(resp.split(':')[-1].strip('T\n'))
        return resp
    
    def read_vector(self):
        val_x = self.read_fvalueX()
        val_y = self.read_fvalueY()
        val_z = self.read_fvalueZ()
        return [val_x, val_y, val_z]
        
    def write_fvalueX(self, val):
        cmd = 'SET:DEV:GRPX:PSU:SIG:FSET:' + str(val) + '\r\n'
        self.s.sendall(cmd.encode())
        self.s.recv(1400)
        # We also want the magnet to go to this setpoint, so
        self.s.sendall('SET:DEV:GRPX:PSU:ACTN:RTOS\r\n'.encode())
        self.s.recv(1400)

    def write_fvalueY(self, val):
        cmd = 'SET:DEV:GRPY:PSU:SIG:FSET:' + str(val) + '\r\n'
        self.s.sendall(cmd.encode())
        self.s.recv(1400)
        # We also want the magnet to go to this setpoint, so
        self.s.sendall('SET:DEV:GRPY:PSU:ACTN:RTOS\r\n'.encode())
        self.s.recv(1400)

    def write_fvalueZ(self, val):
        cmd = 'SET:DEV:GRPZ:PSU:SIG:FSET:' + str(val) + '\r\n'
        self.s.sendall(cmd.encode())
        self.s.recv(1400)
        # We also want the magnet to go to this setpoint, so
        self.s.sendall('SET:DEV:GRPZ:PSU:ACTN:RTOS\r\n'.encode())
        self.s.recv(1400)        
    
    def write_vector(self, val):
        if len(val) == 3:
            self.write_fvalueX(val[0])
            self.write_fvalueY(val[1])
            self.write_fvalueZ(val[2])
    
    def read_rateX(self):
        self.s.sendall('READ:DEV:GRPX:PSU:SIG:RFST\r\n'.encode())
        resp = self.s.recv(1400).decode()
        resp = float(resp.split(':')[-1].strip('T/m\n'))
        return resp
    
    def read_rateY(self):
        self.s.sendall('READ:DEV:GRPY:PSU:SIG:RFST\r\n'.encode())
        resp = self.s.recv(1400).decode()
        resp = float(resp.split(':')[-1].strip('T/m\n'))
        return resp
    
    def read_rateZ(self):
        self.s.sendall('READ:DEV:GRPZ:PSU:SIG:RFST\r\n'.encode())
        resp = self.s.recv(1400).decode()
        resp = float(resp.split(':')[-1].strip('T/m\n'))
        return resp
    
    def read_rates(self):
        rate_x = self.read_rateX()
        rate_y = self.read_rateY()
        rate_z = self.read_rateZ()
        return [rate_x, rate_y, rate_z]
    
    def write_rateX(self, val):
        cmd = 'SET:DEV:GRPX:PSU:SIG:RFST:' + str(val) + '\r\n'
        self.s.sendall(cmd.encode())
        self.s.recv(1400)
        
    def write_rateY(self, val):
        cmd = 'SET:DEV:GRPY:PSU:SIG:RFST:' + str(val) + '\r\n'
        self.s.sendall(cmd.encode())
        self.s.recv(1400)
        
    def write_rateZ(self, val):
        cmd = 'SET:DEV:GRPZ:PSU:SIG:RFST:' + str(val) + '\r\n'
        self.s.sendall(cmd.encode())
        self.s.recv(1400)
        
    def read_state(self):
        # Human-readable response of the magnet state
        self.s.sendall('READ:DEV:GRPX:PSU:ACTN\r\n'.encode())
        respX = self.s.recv(1400).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:GRPY:PSU:ACTN\r\n'.encode())
        respY = self.s.recv(1400).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:GRPZ:PSU:ACTN\r\n'.encode())
        respZ = self.s.recv(1400).decode().split(':')[-1].strip('\n')      
        msg = '(X) : ' + respX + ', (Y) : ' + respY + ', (Z) : ' + respZ
        return msg
    
    def read_temp(self):
        self.s.sendall('READ:DEV:MB1.T1:TEMP:SIG:TEMP\r\n'.encode())
        resp = self.s.recv(1400).decode()
        resp = float(resp.split(':')[-1].strip('K\n'))
        return resp
    
    def read_status(self):
        # Software response of the magnet state
        self.s.sendall('READ:DEV:GRPX:PSU:ACTN\r\n'.encode())
        respX = self.s.recv(1400).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:GRPY:PSU:ACTN\r\n'.encode())
        respY = self.s.recv(1400).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:GRPZ:PSU:ACTN\r\n'.encode())
        respZ = self.s.recv(1400).decode().split(':')[-1].strip('\n') 
        if respX == 'HOLD' and respY == 'HOLD' and respZ == 'HOLD':
            return 'HOLD'
        if respX != 'HOLD' or respY != 'HOLD' or respZ != 'HOLD':
            return 'MOVING'
        
    def read_alarm(self):
        self.s.sendall('READ:SYS:ALRM\r\n'.encode())
        resp = self.s.recv(1400).decode()
        return resp
    
    def gotozero(self):
        self.s.sendall('SET:DEV:GRPX:PSU:ACTN:RTOZ\r\n'.encode())
        self.s.recv(1400)
        self.s.sendall('SET:DEV:GRPY:PSU:ACTN:RTOZ\r\n'.encode())
        self.s.recv(1400)
        self.s.sendall('SET:DEV:GRPZ:PSU:ACTN:RTOZ\r\n'.encode())
        self.s.recv(1400)
        
    def clamp(self):
        self.s.sendall('SET:DEV:GRPX:PSU:ACTN:CLMP\r\n'.encode())
        self.s.recv(1400)
        self.s.sendall('SET:DEV:GRPY:PSU:ACTN:CLMP\r\n'.encode())
        self.s.recv(1400)
        self.s.sendall('SET:DEV:GRPZ:PSU:ACTN:CLMP\r\n'.encode())
        self.s.recv(1400)   
        
    def hold(self):
        self.s.sendall('SET:DEV:GRPX:PSU:ACTN:HOLD\r\n'.encode())
        self.s.recv(1400)
        self.s.sendall('SET:DEV:GRPY:PSU:ACTN:HOLD\r\n'.encode())
        self.s.recv(1400)
        self.s.sendall('SET:DEV:GRPZ:PSU:ACTN:HOLD\r\n'.encode())
        self.s.recv(1400)        
        
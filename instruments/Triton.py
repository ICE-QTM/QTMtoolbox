# -*- coding: utf-8 -*-
"""
Module to interact with the Oxford Triton controller pc.
Uses TCP/IP sockets to communicate with the GPIB device.

Version 2.0 (2020-09-14)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import socket

def convertUnits(val):
    if val[-1] == 'n':
        val = float(val[:-1] + 'E-9')
    elif val[-1] == 'u':
        val = float(val[:-1] + 'E-6')
    elif val[-1] == 'm':
        val = float(val[:-1] + 'E-3')
    return val
        

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not an Oxford Triton controller. Please retry with the correct
    address. Make sure that each device has an unique address.
    """
    pass

class Triton:
    type = 'Oxford Triton'

    def __init__(self, IPaddress, port=33576):
        # Port should be a number, not a string
        if not isinstance(port, int):
            port = int(port)
        # Prepare socket instance
        self.s = socket.socket()
        self.s.connect((IPaddress, port))

    def close(self):
        self.s.close()

    def query(self, val):
        self.s.sendall((val + '\r\n').encode())
        resp = self.s.recv(1024).decode()
        return resp

    def read_temp5(self):
        self.s.sendall('READ:DEV:T5:TEMP:SIG:TEMP\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return float(resp)

    def read_temp8(self):
        self.s.sendall('READ:DEV:T8:TEMP:SIG:TEMP\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return float(resp)

    def read_temp11(self):
        self.s.sendall('READ:DEV:T11:TEMP:SIG:TEMP\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return float(resp)

    def write_Tset5(self, val):
        self.s.sendall(('SET:DEV:T5:TEMP:LOOP:TSET:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1024).decode()

    def write_Tset8(self, val):
        self.s.sendall(('SET:DEV:T8:TEMP:LOOP:TSET:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1024).decode()

    def read_Tset5(self):
        self.s.sendall('READ:DEV:T5:TEMP:LOOP:TSET\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return float(resp)

    def read_Tset8(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:TSET\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return float(resp)

    def write_range5(self, val):
        self.s.sendall(('SET:DEV:T5:TEMP:LOOP:RANGE:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1024).decode()

    def read_range5(self):
        self.s.sendall('READ:DEV:T5:TEMP:LOOP:RANGE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('A\n')
        if resp == 'NOT_FOUND':
            print('The Triton RI was unable to provide the range. Please check what control channel you are using.')
        else:
            resp = convertUnits(resp)
        return resp

    def write_range8(self, val):
        self.s.sendall(('SET:DEV:T8:TEMP:LOOP:RANGE:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1024).decode()

    def read_range8(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:RANGE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('A\n')
        if resp == 'NOT_FOUND':
            print('The Triton RI was unable to provide the range. Please check what control channel you are using.')
        else:
            resp = convertUnits(resp)
        return resp

    def loop_on(self):
        self.s.sendall('SET:DEV:T8:TEMP:LOOP:MODE:ON\r\n'.encode())
        resp = self.s.recv(1024).decode()

    def loop_off(self):
        self.s.sendall('SET:DEV:T8:TEMP:LOOP:MODE:OFF\r\n'.encode())
        resp = self.s.recv(1024).decode()

    def read_loop(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:MODE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return resp

    def write_Trate(self, val):
        self.s.sendall(('SET:DEV:T8:TEMP:LOOP:RAMP:RATE:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1024).decode()

    def read_Trate(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:RAMP:RATE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return resp

    def write_Hchamber(self, val):
        self.s.sendall(('SET:DEV:H1:HTR:SIG:POWR:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1024).decode()

    def read_Hchamber(self):
        self.s.sendall('READ:DEV:H1:HTR:SIG:POWR\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('W\n')
        resp = convertUnits(resp)
        return resp

    def write_Hstill(self, val):
        self.s.sendall(('SET:DEV:H2:HTR:SIG:POWR:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1024).decode()

    def read_Hstill(self):
        self.s.sendall('READ:DEV:H2:HTR:SIG:POWR\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('W\n')
        resp = convertUnits(resp)
        return resp

    def read_Tchan(self):
        # This command returns INVALID, but should work according to the RI manual
        self.s.sendall('READ:DEV:T5:TEMP:LOOP:CHAN\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1]
        return resp
    
    def read_PID5(self):
        self.s.sendall('READ:DEV:T5:TEMP:LOOP:P\r\n'.encode())
        p = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:T5:TEMP:LOOP:I\r\n'.encode())
        i = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:T5:TEMP:LOOP:D\r\n'.encode())
        d = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return [p, i, d]
    
    def read_PID8(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:P\r\n'.encode())
        p = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:I\r\n'.encode())
        i = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:D\r\n'.encode())
        d = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return [p, i, d]
    
    def write_PID5(self, p, i, d):
        self.s.sendall('SET:DEV:T5:TEMP:LOOP:P:' + str(p) + '\r\n'.encode())
        self.s.recv(1024)
        self.s.sendall('SET:DEV:T5:TEMP:LOOP:I:' + str(i) + '\r\n'.encode())
        self.s.recv(1024)
        self.s.sendall('SET:DEV:T5:TEMP:LOOP:D:' + str(d) + '\r\n'.encode())
        self.s.recv(1024)
        
    def write_PID8(self, p, i, d):
        self.s.sendall('SET:DEV:T8:TEMP:LOOP:P:' + str(p) + '\r\n'.encode())
        self.s.recv(1024)
        self.s.sendall('SET:DEV:T8:TEMP:LOOP:I:' + str(i) + '\r\n'.encode())
        self.s.recv(1024)
        self.s.sendall('SET:DEV:T8:TEMP:LOOP:D:' + str(d) + '\r\n'.encode())
        self.s.recv(1024)
        
    def read_status(self):
        self.s.sendall('READ:SYS:DR:STATUS\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return resp  

    def read_action(self):
        self.s.sendall('READ:SYS:DR:ACTN\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        if resp == 'PCL':
            return 'Precooling'
        elif resp == 'EPCL':
            return 'Empty precool loop'
        elif resp == 'COND':
            return 'Condensing'
        elif resp == 'NONE':
            if self.read_temp5() < 1.5:
                return 'Condensing and circulating'
            else:
                return 'Idle'
        elif resp == 'COLL':
            return 'Collecting the mixture'
        else:
            return 'Unknown'
      
    def read_pres1(self):
        self.s.sendall('READ:DEV:P1:PRES:SIG:PRES\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('B\n')
        resp = convertUnits(resp)
        return resp  
    
    def read_pres2(self):
        self.s.sendall('READ:DEV:P2:PRES:SIG:PRES\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('B\n')
        resp = convertUnits(resp)
        return resp   
    
    def read_pres3(self):
        self.s.sendall('READ:DEV:P3:PRES:SIG:PRES\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('B\n')
        resp = convertUnits(resp)
        return resp   
    
    def read_pres4(self):
        self.s.sendall('READ:DEV:P4:PRES:SIG:PRES\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('B\n')
        resp = convertUnits(resp)
        return resp   
    
    def read_pres5(self):
        self.s.sendall('READ:DEV:P5:PRES:SIG:PRES\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('B\n')
        resp = convertUnits(resp)
        return resp   
    
    def read_turbspeed(self):
        self.s.sendall('READ:DEV:TURB1:PUMP:SIG:SPD\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('Hz\n')
        return resp  
    
    def read_turbstate(self):
        self.s.sendall('READ:DEV:TURB1:PUMP:SIG:STATE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return resp     

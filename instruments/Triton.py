# -*- coding: utf-8 -*-
"""
Module to interact with the Oxford Triton controller pc.
Uses TCP/IP sockets to communicate with the GPIB device.

Version 1.0 (2018-09-21)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import socket

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not an Oxford Triton controller. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
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

    def read_temp5(self):
        self.s.sendall('READ:DEV:T5:TEMP:SIG:TEMP\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def read_temp8(self):
        self.s.sendall('READ:DEV:T8:TEMP:SIG:TEMP\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def read_temp11(self):
        self.s.sendall('READ:DEV:T11:TEMP:SIG:TEMP\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def write_PID5(self, val):
        self.s.sendall(('SET:DEV:T5:TEMP:LOOP:TSET:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1400).decode()

    def write_PID8(self, val):
        self.s.sendall(('SET:DEV:T8:TEMP:LOOP:TSET:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1400).decode()

    def read_PID5(self):
        self.s.sendall('READ:DEV:T5:TEMP:LOOP:TSET\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def read_PID8(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:TSET\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def write_range(self, val):
        self.s.sendall(('SET:DEV:T8:TEMP:LOOP:RANGE:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1400).decode()

    def read_range(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:RANGE\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def loop_on(self):
        self.s.sendall('SET:DEV:T8:TEMP:LOOP:MODE:ON\r\n'.encode())
        resp = self.s.recv(1400).decode()

    def loop_off(self):
        self.s.sendall('SET:DEV:T8:TEMP:LOOP:MODE:OFF\r\n'.encode())
        resp = self.s.recv(1400).decode()

    def read_loop(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:MODE\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def write_Trate(self, val):
        self.s.sendall(('SET:DEV:T8:TEMP:LOOP:RAMP:RATE:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1400).decode()

    def read_Trate(self):
        self.s.sendall('READ:DEV:T8:TEMP:LOOP:RAMP:RATE\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

    def write_H1(self, val):
        self.s.sendall(('SET:DEV:H1:HTR:SIG:POWR:' + str(val) + '\r\n').encode())
        resp = self.s.recv(1400).decode()

    def read_H1(self):
        self.s.sendall('READ:DEV:H1:HTR:SIG:POWR\r\n'.encode())
        resp = self.s.recv(1400).decode().split(':')[-1].strip('K\n')
        return resp

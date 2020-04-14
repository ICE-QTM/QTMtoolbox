# -*- coding: utf-8 -*-
"""
Module to interact with the Oxford MercuryiPS.
Uses GPIB to communicate with the device.

Version 1.1 (2020-04-14)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa
import time

class MercuryiPS:
    type = 'MercuryiPS'
        
    def __init__(self):
        rm = visa.ResourceManager()
        self.visa = rm.open_resource('GPIB0::1::1::INSTR')  

    def close(self):
        self.visa.close()
        
    def visa_query(self, val):
        cmd = val + '\n'
        resp = self.visa.query(cmd)
        return resp

    def get_iden(self):
        resp = self.visa.query('*IDN?')
        return resp
    
    def read_fvalueX(self):
        resp = self.visa.query('READ:DEV:GRPX:PSU:SIG:FLD')
        resp = float(resp.split(':')[-1].strip('T\n'))
        return resp
    
    def read_fvalueY(self):
        resp = self.visa.query('READ:DEV:GRPY:PSU:SIG:FLD')
        resp = float(resp.split(':')[-1].strip('T\n'))
        return resp
    
    def read_fvalueZ(self):
        resp = self.visa.query('READ:DEV:GRPZ:PSU:SIG:FLD')
        resp = float(resp.split(':')[-1].strip('T\n'))
        return resp
        
    def read_vector(self):
        val_x = self.read_fvalueX()
        val_y = self.read_fvalueY()
        val_z = self.read_fvalueZ()
        return [val_x, val_y, val_z]
    
    def write_fvalueX(self, val):
        self.visa.query('SET:DEV:GRPX:PSU:SIG:FSET:' + str(val))
        time.sleep(0.5)
        self.visa.query('SET:DEV:GRPX:PSU:ACTN:RTOS')
 
    def write_fvalueY(self, val):
        self.visa.query('SET:DEV:GRPY:PSU:SIG:FSET:' + str(val))
        time.sleep(0.5)
        self.visa.query('SET:DEV:GRPY:PSU:ACTN:RTOS')

    def write_fvalueZ(self, val):
        self.visa.query('SET:DEV:GRPZ:PSU:SIG:FSET:' + str(val))
        time.sleep(0.5)
        self.visa.query('SET:DEV:GRPZ:PSU:ACTN:RTOS')
    
    def write_vector(self, val):
        if len(val) == 3:
            self.write_fvalueX(val[0])
            self.write_fvalueY(val[1])
            self.write_fvalueZ(val[2])
    
    def read_rateX(self):
        resp = self.visa.query('READ:DEV:GRPX:PSU:SIG:RFST')
        resp = float(resp.split(':')[-1].strip('T/m\n'))
        return resp

    def read_rateY(self):
        resp = self.visa.query('READ:DEV:GRPY:PSU:SIG:RFST')
        resp = float(resp.split(':')[-1].strip('T/m\n'))
        return resp
    
    def read_rateZ(self):
        resp = self.visa.query('READ:DEV:GRPZ:PSU:SIG:RFST')
        resp = float(resp.split(':')[-1].strip('T/m\n'))
        return resp
    
    def read_rates(self):
        rate_x = self.read_rateX()
        rate_y = self.read_rateY()
        rate_z = self.read_rateZ()
        return [rate_x, rate_y, rate_z]
    
    def write_rateX(self, val):
        self.visa.query('SET:DEV:GRPX:PSU:SIG:RFST:' + str(val))
    
    def write_rateY(self, val):
        self.visa.query('SET:DEV:GRPY:PSU:SIG:RFST:' + str(val))
        
    def write_rateZ(self, val):
        self.visa.query('SET:DEV:GRPZ:PSU:SIG:RFST:' + str(val))
    
    def read_state(self):
        respX = self.visa.query('READ:DEV:GRPX:PSU:ACTN').split(':')[-1].strip('\n')
        time.sleep(0.05)
        respY = self.visa.query('READ:DEV:GRPY:PSU:ACTN').split(':')[-1].strip('\n')
        time.sleep(0.05)
        respZ = self.visa.query('READ:DEV:GRPZ:PSU:ACTN').split(':')[-1].strip('\n')
        msg = '(X) : ' + respX + ', (Y) : ' + respY + ', (Z) : ' + respZ
        return msg
    
    def read_temp(self):
        resp = self.visa.query('READ:DEV:MB1.T1:TEMP:SIG:TEMP')
        resp = float(resp.split(':')[-1].strip('K\n'))
        return resp    

    def read_status(self):
        respX = self.visa.query('READ:DEV:GRPX:PSU:ACTN').split(':')[-1].strip('\n')
        time.sleep(0.05)
        respY = self.visa.query('READ:DEV:GRPY:PSU:ACTN').split(':')[-1].strip('\n')
        time.sleep(0.05)
        respZ = self.visa.query('READ:DEV:GRPZ:PSU:ACTN').split(':')[-1].strip('\n')
        if respX == 'HOLD' and respY == 'HOLD' and respZ == 'HOLD':
            return 'HOLD'
        if respX != 'HOLD' or respY != 'HOLD' or respZ != 'HOLD':
            return 'MOVING'

    def read_alarm(self):
        resp = self.visa.query('READ:SYS:ALRM')
        return resp
    
    def gotozero(self):
        self.visa.query('SET:DEV:GRPX:PSU:ACTN:RTOZ')
        time.sleep(0.05)
        self.visa.query('SET:DEV:GRPY:PSU:ACTN:RTOZ')
        time.sleep(0.05)
        self.visa.query('SET:DEV:GRPZ:PSU:ACTN:RTOZ')        

    def clamp(self):
        self.visa.query('SET:DEV:GRPX:PSU:ACTN:CLMP')
        time.sleep(0.05)
        self.visa.query('SET:DEV:GRPY:PSU:ACTN:CLMP')
        time.sleep(0.05)
        self.visa.query('SET:DEV:GRPZ:PSU:ACTN:CLMP')
        
    def hold(self):
        self.visa.query('SET:DEV:GRPX:PSU:ACTN:HOLD')
        time.sleep(0.05)
        self.visa.query('SET:DEV:GRPY:PSU:ACTN:HOLD')
        time.sleep(0.05)
        self.visa.query('SET:DEV:GRPZ:PSU:ACTN:HOLD')
        
    def read_setpX(self):
        resp = self.visa.query('READ:DEV:GRPX:PSU:SIG:FSET')
        return float(resp.split(':')[-1].strip('T\n'))
    
    def read_setpY(self):
        resp = self.visa.query('READ:DEV:GRPY:PSU:SIG:FSET')
        return float(resp.split(':')[-1].strip('T\n'))
    
    def read_setpZ(self):
        resp = self.visa.query('READ:DEV:GRPZ:PSU:SIG:FSET')
        return float(resp.split(':')[-1].strip('T\n'))

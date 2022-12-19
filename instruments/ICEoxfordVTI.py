# -*- coding: utf-8 -*-
"""
Module to interact with the ICEoxford VTI Remote Comms service.
Uses TCP/IP sockets to communicate with the device.

Version 1.0 (2022-12-19)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl
"""

import socket

class ICEoxfordVTI:
    type = 'ICEoxford VTI'

    def __init__(self, IPaddress, port=6340):
        # Port should be a number, not a string
        if not isinstance(port, int):
            port = int(port)
        # Prepare socket instance
        self.s = socket.socket()
        self.s.connect((IPaddress, port))
        
        # Check if LEMON is connected, otherwise connect
        self.s.sendall(('LEMON CONNECTED?\r\n').encode())
        resp = self.s.recv(1024).decode()
        if resp == 'LEMON CONNECTED':
            print('ICEoxford LEMON software connected.')
        else:
            print('ICEoxford LEMON software not connected. Connecting...')
            self.s.sendall(('CONNECT LEMON\r\n').encode())
            self.s.recv(1024).decode()

    def close(self):
        # We also disconnect the LEMON software here
        self.s.sendall(('DISCONNECT LEMON\r\n').encode())
        self.s.recv(1024).decode()
        self.s.close()

    def query(self, val):
        self.s.sendall((val + '\r\n').encode())
        resp = self.s.recv(1024).decode()
        return resp 
    
    def overview(self):
        # Get all attributes from self that contain '_read'
        attr_list = [attr for attr in dir(self) if 'read_' in attr]
        # Loop over every item, print results
        for attr in attr_list:
            print(attr + ': ' + str(getattr(self, attr)()))
        
    # LEMON commands ---------------------------------------------------------------------------   
    def LEMON_connect(self):
        self.s.sendall(('CONNECT LEMON\r\n').encode())
        self.s.recv(1024).decode()
        
    def LEMON_disconnect(self):
        self.s.sendall(('DISCONNECT LEMON\r\n').encode())
        self.s.recv(1024).decode()

    def LEMON_status(self):
        self.s.sendall(('LEMON CONNECTED?\r\n').encode())
        resp = self.s.recv(1024).decode().strip('\r\n') 
        return resp

    # Needle valve commands --------------------------------------------------------------------
    # Needle valve mode, can be AUTO or MANUAL    
    def read_NV1mode(self):
        self.s.sendall(('NV1 MODE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp    
  
    def read_NV2mode(self):
        self.s.sendall(('NV2 MODE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp  
    
    def write_NV1mode(self, val):
        if val in ['MANUAL', 'AUTO']:
            self.s.sendall(('NV1 MODE=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('NV1 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The needle valve mode can be "MANUAL" or "AUTO".')   

    def write_NV2mode(self, val):
        if val in ['MANUAL', 'AUTO']:
            self.s.sendall(('NV2 MODE=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('NV2 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The needle valve mode can be "MANUAL" or "AUTO".')
    
    # Needle valve manual output set value as percentage
    def read_NV1manout(self):
        self.s.sendall(('NV1 MAN OUT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)
    
    def read_NV2manout(self):
        self.s.sendall(('NV2 MAN OUT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 
    
    def write_NV1manout(self, val):
        self.s.sendall(('NV1 MAN OUT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV1 SET VALUES\r\n').encode())
        self.s.recv(1024)

    def write_NV2manout(self, val):
        self.s.sendall(('NV2 MAN OUT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV2 SET VALUES\r\n').encode())
        self.s.recv(1024)
    
    # Needle valve setpoint in mbar
    def read_NV1setp(self):
        self.s.sendall(('NV1 SETPOINT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)    
    
    def read_NV2setp(self):
        self.s.sendall(('NV2 SETPOINT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 
    
    def write_NV1setp(self, val):
        self.s.sendall(('NV1 SETPOINT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV1 SET VALUES\r\n').encode())
        self.s.recv(1024)

    def write_NV2setp(self, val):
        self.s.sendall(('NV2 SETPOINT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV2 SET VALUES\r\n').encode())
        self.s.recv(1024) 
        
    # Needle valve PID settings as a list [P, I, D]
    def read_NV1PID(self):
        self.s.sendall(('NV1 PID?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        resp = resp.split(',')
        for i in range(3):
            resp[i] = float(resp[i])
        return resp     
    
    def read_NV2PID(self):
        self.s.sendall(('NV1 PID?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        resp = resp.split(',')
        for i in range(3):
            resp[i] = float(resp[i])
        return resp 
    
    def write_NV1PID(self, P, I, D):
        self.s.sendall(('NV1 PID=' + str(P) + ',' + str(I) + ',' + str(D) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV1 SET VALUES\r\n').encode())
        self.s.recv(1024)

    def write_NV2PID(self, P, I, D):
        self.s.sendall(('NV2 PID=' + str(P) + ',' + str(I) + ',' + str(D) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV2 SET VALUES\r\n').encode())
        self.s.recv(1024)
        
    # Needle valve error band in mbar
    def read_NV1error(self):
        self.s.sendall(('NV1 ERROR BAND?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)    
    
    def read_NV2error(self):
        self.s.sendall(('NV2 ERROR BAND?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 
    
    def write_NV1error(self, val):
        self.s.sendall(('NV1 ERROR BAND=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV1 SET VALUES\r\n').encode())
        self.s.recv(1024)

    def write_NV2error(self, val):
        self.s.sendall(('NV2 ERROR BAND=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('NV2 SET VALUES\r\n').encode())
        self.s.recv(1024) 

    # Needle valve setpoint in mbar
    def read_NV1outp(self):
        self.s.sendall(('NV OUTPUT 1?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)    
    
    def read_NV2outp(self):
        self.s.sendall(('NV OUTPUT 2?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)      
    
    # Heaters commands --------------------------------------------------------------------------
    # Heater mode, can be AUTO or MANUAL    
    def read_H1mode(self):
        self.s.sendall(('HEATER1 MODE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp    
  
    def read_H2mode(self):
        self.s.sendall(('HEATER2 MODE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp  
    
    def write_H1mode(self, val):
        if val in ['MANUAL', 'AUTO']:
            self.s.sendall(('HEATER1 MODE=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('HEATER1 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The heater mode can be "MANUAL" or "AUTO".')   

    def write_H2mode(self, val):
        if val in ['MANUAL', 'AUTO']:
            self.s.sendall(('HEATER2 MODE=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('HEATER2 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The heater mode can be "MANUAL" or "AUTO".')   
    
    # Heater channel, returns the chosen control channel   
    def read_H1chan(self):
        self.s.sendall(('HEATER1 CHAN?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp        
  
    def read_H2chan(self):
        self.s.sendall(('HEATER2 CHAN?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp 

    def write_H1chan(self, val):
        if val in ['NONE', 'A', 'B', 'C', 'D', 'D2', 'D3', 'D4', 'D5']:
            self.s.sendall(('HEATER1 CHAN=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('HEATER1 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The heater channel can be "NONE", "A", "B", "C", "D", "D2", "D3", "D4", "D5".')    

    def write_H2chan(self, val):
        if val in ['NONE', 'A', 'B', 'C', 'D', 'D2', 'D3', 'D4', 'D5']:
            self.s.sendall(('HEATER2 CHAN=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('HEATER2 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The heater channel can be "NONE", "A", "B", "C", "D", "D2", "D3", "D4", "D5".') 
    
    # Heater channel manual output, returns output as percentage  
    def read_H1manout(self):
        self.s.sendall(('HEATER1 MAN OUT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)
  
    def read_H2manout(self):
        self.s.sendall(('HEATER2 MAN OUT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)
                     
    def write_H1manout(self, val):
        self.s.sendall(('HEATER1 MAN OUT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('HEATER1 SET VALUES\r\n').encode())
        self.s.recv(1024)

    def write_H2manout(self, val):
        self.s.sendall(('HEATER2 MAN OUT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('HEATER2 SET VALUES\r\n').encode())
        self.s.recv(1024)
    
    # Heater channel setpoint, returns value in Kelvin
    def read_H1setp(self):
        self.s.sendall(('HEATER1 SETPOINT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)
  
    def read_H2setp(self):
        self.s.sendall(('HEATER2 SETPOINT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)  

    def write_H1setp(self, val):
        self.s.sendall(('HEATER1 SETPOINT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('HEATER1 SET VALUES\r\n').encode())
        self.s.recv(1024)
    
    def write_H2setp(self, val):
        self.s.sendall(('HEATER2 SETPOINT=' + str(val) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('HEATER2 SET VALUES\r\n').encode())
        self.s.recv(1024)
    
    # Heater channel ramp rate, returns value in Kelvin/minute
    def read_H1rate(self):
        self.s.sendall(('HEATER1 RAMP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)
  
    def read_H2rate(self):
        self.s.sendall(('HEATER2 RAMP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)     
    
    # Heater PID settings as a list [P, I, D]
    def read_H1PID(self):
        self.s.sendall(('HEATER1 PID?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        resp = resp.split(',')
        for i in range(3):
            resp[i] = float(resp[i])
        return resp     
    
    def read_H2PID(self):
        self.s.sendall(('HEATER2 PID?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        resp = resp.split(',')
        for i in range(3):
            resp[i] = float(resp[i])
        return resp

    def write_H1PID(self, P, I, D):
        self.s.sendall(('HEATER1 PID=' + str(P) + ',' + str(I) + ',' + str(D) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('HEATER1 SET VALUES\r\n').encode())
        self.s.recv(1024)

    def write_H2PID(self, P, I, D):
        self.s.sendall(('HEATER2 PID=' + str(P) + ',' + str(I) + ',' + str(D) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('HEATER2 SET VALUES\r\n').encode())
        self.s.recv(1024)
    
    # Heater channel range, returns OFF, LOW, MED, HIGH
    def read_H1range(self):
        self.s.sendall(('HEATER1 RANGE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp
  
    def read_H2range(self):
        self.s.sendall(('HEATER2 RANGE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    def write_H1range(self, val):
        if val in ['OFF', 'LOW', 'MEDIUM', 'HIGH']:
            self.s.sendall(('HEATER1 RANGE=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('HEATER1 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The heater range can be either "OFF", "LOW", "MEDIUM" or "HIGH".')

    def write_H2range(self, val):
        if val in ['OFF', 'LOW', 'MEDIUM', 'HIGH']:
            self.s.sendall(('HEATER2 RANGE=' + val + '\r\n').encode())
            self.s.recv(1024)
            self.s.sendall(('HEATER2 SET VALUES\r\n').encode())
            self.s.recv(1024)
        else:
            raise ValueError('The heater range can be either "OFF", "LOW", "MEDIUM" or "HIGH".')
    
    # Heater channel ramp enabled, returns OFF, ON
    def read_H1ramp(self):
        self.s.sendall(('HEATER1 SETPOINT RAMP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp
  
    def read_H2ramp(self):
        self.s.sendall(('HEATER2 SETPOINT RAMP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp     
    
    # Gas box commands --------------------------------------------------------------------------
    # Valve status, can be CLOSED, OPEN    
    def read_SV1(self):
        self.s.sendall(('GB SV1?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp    

    def read_SV2(self):
        self.s.sendall(('GB SV2?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   

    def read_SV3(self):
        self.s.sendall(('GB SV3?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   

    def read_SV4(self):
        self.s.sendall(('GB SV4?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   

    def read_pump(self):
        self.s.sendall(('GB PUMP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   

    # Dump pressure in mbar
    def read_dump(self):
        self.s.sendall(('DUMP PRESSURE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)       

    # Sample space pressure in mbar
    def read_samp(self):
        self.s.sendall(('SAMPLE SPACE PRESSURE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)  
    
    # Circulation pressure in mbar
    def read_circ(self):
        self.s.sendall(('CIRCULATION PRESSURE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)  
    
    # Temperature commands --------------------------------------------------------------------------
    # Read temperature channels, value in Kelvin   
    def read_tempA(self):
        self.s.sendall(('TEMPERATURE A?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp    
    
    def read_tempB(self):
        self.s.sendall(('TEMPERATURE B?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    def read_tempC(self):
        self.s.sendall(('TEMPERATURE C?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    def read_tempD1(self):
        self.s.sendall(('TEMPERATURE D1?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    def read_tempD2(self):
        self.s.sendall(('TEMPERATURE D2?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    def read_tempD3(self):
        self.s.sendall(('TEMPERATURE D3?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    def read_tempD4(self):
        self.s.sendall(('TEMPERATURE D4?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    def read_tempD5(self):
        self.s.sendall(('TEMPERATURE D5?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp   
    
    # Magnet commands --------------------------------------------------------------------------
    # Magnet lower sweep current limit, value in Ampere  
    def read_maglow(self):
        self.s.sendall(('MAGNET LOWER SWEEP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)     

    # Magnet upper sweep current limit, value in Ampere   
    def read_magupp(self):
        self.s.sendall(('MAGNET LOWER SWEEP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)     

    # Magnet voltage limit, value in Volt 
    def read_magvolt(self):
        self.s.sendall(('MAGNET VOLTAGE?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)    
    
    # Magnet current ranges, value in Ampere 
    def read_magrange0(self):
        self.s.sendall(('MAGNET RANGE 0?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)     

    def read_magrange1(self):
        self.s.sendall(('MAGNET RANGE 1?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 

    def read_magrange2(self):
        self.s.sendall(('MAGNET RANGE 2?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 

    # Magnet current range rates, value in Ampere/second 
    def read_magrate0(self):
        self.s.sendall(('MAGNET RATE 0?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)     

    def read_magrate1(self):
        self.s.sendall(('MAGNET RATE 1?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 

    def read_magrate2(self):
        self.s.sendall(('MAGNET RATE 2?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp)

    # Magnet sweep mode 
    def read_magmode(self):
        self.s.sendall(('MAGNET SWEEP?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp

    # Magnet output field, value in Tesla
    def read_magfield(self):
        self.s.sendall(('MAGNET FIELD?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 

    # Magnet power supply output current, value in Ampere
    def read_magoutpcurr(self):
        self.s.sendall(('MAGNET OUTPUT CURRENT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 

    # Magnet lead current, value in Ampere
    def read_magleadcurr(self):
        self.s.sendall(('MAGNET CURRENT?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return float(resp) 

    # Magnet quench status, can be QUENCH, NO QUENCH
    def read_magquench(self):
        self.s.sendall(('MAGNET QUENCH?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp 

    # Magnet persistent mode heater, can be ON, OFF
    def read_magheater(self):
        self.s.sendall(('MAGNET HEATER?\r\n').encode())
        resp = self.s.recv(1024).decode().split('=')[1].strip('\r\n')
        return resp 

# -*- coding: utf-8 -*-
"""
Module to interact with the Oxford Triton controller pc.
Uses TCP/IP sockets to communicate with the GPIB device.

Version 3.1.1 (2023-06-23)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl

----------------------------------------------------------------------------
The latest version (3.0 and above) uses Python's "exec" function
to reduce the number of lines in the code. Functions that are to be repeated
for many channels (such as read_temp1, read_temp2, ..., read_temp16) are 
generated in an exec loop.
----------------------------------------------------------------------------
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

    # Create functions for reading any temperature sensor (chan. 1-16) in the system
    for i in range(16):
        exec("def read_temp" + str(i+1) + "(self):\n" +
             "    self.s.sendall(('READ:DEV:T" + str(i+1) + ":TEMP:SIG:TEMP\\r\\n').encode())\n" +
             "    resp = self.s.recv(1024).decode().split(':')[-1].strip('K\\n')\n" +
             "    return float(resp)")
    
    # Create functions for reading if any temperature channel is enabled (chan. 1-16) in the system
    for i in range(16):
        exec("def read_Tenab" + str(i+1) + "(self):\n" +
             "    self.s.sendall(('READ:DEV:T" + str(i+1) + ":TEMP:MEAS:ENAB\\r\\n').encode())\n" +
             "    resp = self.s.recv(1024).decode().split(':')[-1].strip('\\n')\n" +
             "    return resp")

    # Create functions for writing whether any temperature channel must be enabled/disabled (chan. 1-16) in the system
    # Provide 'ON' or 'OFF' as <val>          
    for i in range(16):
        exec("def write_Tenab" + str(i+1) + "(self, val):\n" +
             "    self.s.sendall(('SET:DEV:T" + str(i+1) + ":TEMP:MEAS:ENAB:' + str(val) + '\\r\\n').encode())\n" +
             "    resp = self.s.recv(1024).decode()")
        
    # Create functions for reading any pressure sensor (chan. 1-6) in the system
    for i in range(16):
        exec("def read_pres" + str(i+1) + "(self):\n" +
             "    self.s.sendall(('READ:DEV:P" + str(i+1) + ":PRES:SIG:PRES\\r\\n').encode())\n" +
             "    resp = self.s.recv(1024).decode().split(':')[-1].strip('B\\n')\n" +
             "    return convertUnits(resp)")
        
    # Create functions for reading any valve actuator (chan. 1-9) in the system
    for i in range(9):
        exec("def read_valve" + str(i+1) + "(self):\n" +
             "    self.s.sendall(('READ:DEV:V" + str(i+1) + ":VALV:SIG:STATE\\r\\n').encode())\n" +
             "    resp = self.s.recv(1024).decode().split(':')[-1].strip('\\n')\n" +
             "    return resp")
        
    # Create functions for writing whether any valve actuactor must be opened/closed (chan. 1-9) in the system
    # Provide 'OPEN' or 'CLOSE' or 'TOGGLE' as <val>          
    for i in range(16):
        exec("def write_valve" + str(i+1) + "(self, val):\n" +
             "    self.s.sendall(('SET:DEV:V" + str(i+1) + ":VALV:SIG:STATE:' + str(val) + '\\r\\n').encode())\n" +
             "    resp = self.s.recv(1024).decode()")
    
    # Get the temperature control channel    
    def read_Tchan(self):
        for i in range(16):
            self.s.sendall(('READ:DEV:T' + str(i+1) + ':TEMP:LOOP:MODE\r\n').encode())
            msg = self.s.recv(1024).decode().split(':')[-1].strip('A\n')
            if not msg == 'NOT_FOUND':
                resp = i+1
        return resp  
    
    # Select the temperature control channel
    def write_Tchan(self, val):
        self.s.sendall(('SET:DEV:T' + str(val) + ':TEMP:LOOP:HTR:H1\r\n').encode())
        self.s.recv(1024).decode()  
                        
    # Read the temperature setpoint of the heater (using the control channel as read from read_Tchan)
    def read_Tset(self):
        chan = self.read_Tchan()
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:TSET\r\n').encode())
        resp = float(self.s.recv(1024).decode().split(':')[-1].strip('K\n'))
        return resp
        
    # Write the temperature setpoint of the heater (using read_Tchan)
    def write_Tset(self, val):
        chan = self.read_Tchan()
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:TSET:' + str(val) + '\r\n').encode())
        self.s.recv(1024)
    
    # Read PID settings for the heater (using read_Tchan)
    def read_PID(self):
        chan = self.read_Tchan()
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:P\r\n').encode())
        p = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:I\r\n').encode())
        i = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:D\r\n').encode())
        d = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return [p, i, d]
    
    # Write PID settings for the heater (using the control channel from read_Tchan)
    def write_PID(self, p, i, d):
        chan = self.read_Tchan()
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:P:' + str(p) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:I:' + str(i) + '\r\n').encode())
        self.s.recv(1024)
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:D:' + str(d) + '\r\n').encode())
        self.s.recv(1024)

    # Turn on the closed heater loop (using the control channel from read_Tchan)    
    def loop_on(self):
        chan = self.read_Tchan()
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:MODE:ON\r\n').encode())
        self.s.recv(1024)

    # Turn off the closed heater loop (using the control channel from read_Tchan)
    def loop_off(self):
        chan = self.read_Tchan()
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:MODE:OFF\r\n').encode())
        self.s.recv(1024)

    # Read the loop status (from read_Tchan)
    def read_loop(self):
        chan = self.read_Tchan()
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:MODE\r\n').encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        return resp
    
    # Read the heater range (by using read_Tchan)
    def read_range(self):
        chan = self.read_Tchan()
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:RANGE\r\n').encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('A\n')
        return convertUnits(resp)
    
    # Write the heater range (by using read_Tchan)
    def write_range(self, val):
        chan = self.read_Tchan()
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:RANGE: ' + str(val) + '\r\n').encode())
        self.s.recv(1024)

    # Write the temperature control ramp rate (using read_Tchan)
    def write_Trate(self, val):
        chan = self.read_Tchan()
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:RAMP:RATE:' + str(val) + '\r\n').encode())
        self.s.recv(1024)

    # Read the temperature control ramp rate (using read_Tchan)
    def read_Trate(self):
        chan = self.read_Tchan()
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:RAMP:RATE\r\n').encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('K/min\n')
        return resp
    
    # Read the control temperature ramp status (enabled/disabled)
    def read_ratestatus(self):
        chan = self.read_Tchan()
        self.s.sendall(('READ:DEV:T' + str(chan) + ':TEMP:LOOP:RAMP:ENAB\r\n').encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        if resp == 'ON':
            return 1
        elif resp == 'OFF':
            return 0
        else:
            raise ValueError('Expected to receive "ON" or "OFF" but got a different response.')
    
    # Write the control temperature ramp status (use 'ON' or 'OFF' as <val>)
    def write_ratestatus(self, val):
        chan = self.read_Tchan()
        self.s.sendall(('SET:DEV:T' + str(chan) + ':TEMP:LOOP:RAMP:ENAB:' + str(val) + '\r\n').encode())
        self.s.recv(1024)

    def write_Hchamber(self, val):
        # Setpoint is in uW
        self.s.sendall(('SET:DEV:H1:HTR:SIG:POWR:' + str(val) + '\r\n').encode())
        self.s.recv(1024)

    def read_Hchamber(self):
        self.s.sendall('READ:DEV:H1:HTR:SIG:POWR\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('W\n')
        resp = convertUnits(resp)
        return resp

    def write_Hstill(self, val):
        # Setpoint is in uW
        self.s.sendall(('SET:DEV:H2:HTR:SIG:POWR:' + str(val) + '\r\n').encode())
        self.s.recv(1024)

    def read_Hstill(self):
        self.s.sendall('READ:DEV:H2:HTR:SIG:POWR\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('W\n')
        resp = convertUnits(resp)
        return resp
            
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
    
    # Read the speed of the turbo pump
    def read_turbspeed(self):
        self.s.sendall('READ:DEV:TURB1:PUMP:SIG:SPD\r\n'.encode())
        resp = float(self.s.recv(1024).decode().split(':')[-1].strip('Hz\n'))
        return resp  
    
    # Read the status (on/off) of the turbo pump
    def read_turbstate(self):
        self.s.sendall('READ:DEV:TURB1:PUMP:SIG:STATE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return resp  
    
    # Set state of the turbo
    def write_turbstate(self, val):
        self.s.sendall(('SET:DEV:TURB1:PUMP:SIG:STATE:' + val + '\r\n').encode())
        self.s.recv(1024)
    
    # Read the cumulative operational hours of the turbo pump
    def read_turbhours(self):
        self.s.sendall('READ:DEV:TURB1:PUMP:SIG:HRS\r\n'.encode())
        resp = float(self.s.recv(1024).decode().split(':')[-1].strip('h\n'))
        return resp
    
    # Read the status (on/off) of the 3He compressor
    def read_compstate(self):
        self.s.sendall('READ:DEV:COMP:PUMP:SIG:STATE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return resp      

    # Read the status (on/off) of the 3He compressor
    def read_fpstate(self):
        self.s.sendall('READ:DEV:FP:PUMP:SIG:STATE\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        return resp 
    
    # Read the status (on/off) of the PTR compressor
    def read_PTRstate(self):
        self.s.sendall('READ:DEV:C1:PTC\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        # Note that this response gets ALL parameters of the PTR compressor!
        return resp     
    
    # Read the list of assigned temperature channels in the Triton software
    def read_Tchandefs(self):
        self.s.sendall('READ:SYS:DR:CHAN\r\n'.encode())
        resp = self.s.recv(1024).decode().split(':')
        chan_still = 'Still: ' + resp[5][-1]
        chan_mix = 'Mixing chamber: ' + resp[7][-1]
        chan_cool = 'Cooldown: ' + resp[9][-1]
        chan_pt1 = 'PT1: ' + resp[11][-1]
        chan_pt2 = 'PT2: ' + resp[13][-1]
        return [chan_still, chan_mix, chan_cool, chan_pt1, chan_pt2]
    
    def info(self):
        print('-----------------------------------------------------')
        print('System status:               ' + str(self.read_status()))
        print('Automation task:             ' + str(self.read_action()))
        print('-----------------------------------------------------')
        # Get cooldown channel and then request temperature value and status of that channel
        chan_cool = str(self.read_Tchandefs()[2].split(':')[1].strip(' '))
        self.s.sendall(('READ:DEV:T' + str(chan_cool) + ':TEMP:SIG:TEMP\r\n').encode())
        resp1 = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        self.s.sendall(('READ:DEV:T' + str(chan_cool) + ':TEMP:MEAS:ENAB\r\n').encode())
        resp2 = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        print('Cooldown channel temp (' + str(chan_cool) + '):   ' + str(resp1) + ' K, (sensor: ' + resp2 + ')')  
        chan_mix = str(self.read_Tchandefs()[1].split(':')[1].strip(' '))
        self.s.sendall(('READ:DEV:T' + str(chan_mix) + ':TEMP:SIG:TEMP\r\n').encode())
        resp3 = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        self.s.sendall(('READ:DEV:T' + str(chan_mix) + ':TEMP:MEAS:ENAB\r\n').encode())
        resp4 = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        print('Mixing chamber temp (' + str(chan_mix) + '):     ' + str(resp3) + ' K, (sensor: ' + resp4 + ')') 
        print('-----------------------------------------------------')
        print('Tank pressure (P1):          ' + str(self.read_pres1()) + str(' bar'))
        print('Condense pressure (P2):      ' + str(self.read_pres2()) + str(' bar'))
        print('Still pressure (P3):         ' + str(self.read_pres3()) + str(' bar'))
        print('Turbo back pressure (P4):    ' + str(self.read_pres4()) + str(' bar'))
        print('Forepump back pressure (P5): ' + str(self.read_pres5()) + str(' bar'))
        print('OVC pressure (P6):           ' + str(self.read_pres6()) + str(' bar'))
        print('------------------------------------------------------')
        print('Heater mode:                 ' + str(self.read_loop()))
        print('Heater control channel:      ' + str(self.read_Tchan()))
        self.s.sendall(('READ:DEV:T' + str(self.read_Tchan()) + ':TEMP:LOOP:TSET\r\n').encode())
        resp5 = self.s.recv(1024).decode().split(':')[-1].strip('K\n')
        print('Heater setpoint:             ' + str(resp5) + ' K')
        self.s.sendall(('READ:DEV:T' + str(self.read_Tchan()) + ':TEMP:LOOP:RANGE\r\n').encode())
        resp6 = self.s.recv(1024).decode().split(':')[-1].strip('\n')
        print('Heater range:                ' + str(resp6))
        print('------------------------------------------------------')
        print('Valve 1:                     ' + str(self.read_valve1()))
        print('Valve 2:                     ' + str(self.read_valve2()))
        print('Valve 3:                     ' + str(self.read_valve3()))
        print('Valve 4:                     ' + str(self.read_valve4()))
        print('Valve 5:                     ' + str(self.read_valve5()))
        print('Valve 6:                     ' + str(self.read_valve6()))
        print('Valve 7:                     ' + str(self.read_valve7()))
        print('Valve 8:                     ' + str(self.read_valve8()))
        print('Valve 9:                     ' + str(self.read_valve9()))
        print('------------------------------------------------------')
        print('3He compressor:              ' + str(self.read_compstate()))
        print('Forepump:                    ' + str(self.read_fpstate()))
        print('Turbo pump:                  ' + str(self.read_turbstate()) + ' (' + str(self.read_turbspeed()) + ' Hz)')
        print('Pulse tube compressor:       ' + str(self.read_PTRstate()))
        print('------------------------------------------------------')
        
        

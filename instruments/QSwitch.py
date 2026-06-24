# -*- coding: utf-8 -*-
"""
Module to interact with a QM QSwitch.
Uses pyserial to communicate with the USB device.
The device has a USB COM address of the form '<xx>'
<xx> is the COM port number.

Version 1.1 (2026-06-24)
Daan Wielens - Researcher at ICE/QTM
University of Twente

-------------------------------------------------------------

Typical workflow / example:
    
    1. Make sure that external equipment connected to the BNC terminals is at zero bias current/voltage
    2. Unground the device
        qs.unground_all()
    3. Make connections for the sample (i.e. sample pin 14 to BNC terminal 1)
        qs.connect_to_bnc(14, 1)
    4. Check connections
        qs.get_status()
    5. Ramp up bias current/voltage
    6. Run experiments
    7. Ramp down bias current/voltage to prepare for QSwitch changes
    8. Remove connections or reset QSwitch
    8a. Remove connections --> this does not ground the device in the meantime
        qs.disconnect_from_bnc(14, 1)
      Now, connect to something else
    8b. Reset full devices --> grounds (soft-acting GND) device and removes all connections
        qs.reset()
        
-------------------------------------------------------------

"""

import serial
import time

class WrongInstrErr(Exception):
    """
    A connection was established to the instrument, but the instrument
    is not a HP 34401A Multimeter. Please retry with the correct
    GPIB address. Make sure that each device has an unique address.
    """
    pass

class QSwitch:
    def __init__(self, COMport, baudrate=9600, timeout=1):
        self.ser = serial.Serial(
            port='COM' + str(COMport),
            baudrate=baudrate,
            timeout=timeout
        )

        # Give device time to initialize
        time.sleep(0.5)
    
        # Check if device is really a QSwitch
        self.ser.write('*IDN?\n'.encode())
        resp = self.ser.readline().decode().strip()
        model = resp.split(',')[1]
        if model != 'QSwitch':
            raise WrongInstrErr('Expected QSwitch, got {}'.format(resp))

    def write(self, cmd):
        cmd_str = cmd.strip() + "\n"
        self.ser.write(cmd_str.encode())

    def query(self, cmd):
        self.write(cmd)
        return self.ser.readline().decode().strip()

    def close(self):
        self.ser.close()

    def get_iden(self):
        return self.query("*IDN?")

    # Resets device to default state (all BNCs disconnected, all Fisher channels to soft-acting ground (1MOhm to GND))
    def reset(self):
        self.write("*RST")

    # Unground all Fisher (OUT/DUT) pins
    def unground_all(self):
        self.write('open (@1!0:24!0)')
        
    def unground_single(self, val):
        # Only ungrounds channel <val>
        self.write('open (@' + str(val) + '!0)')
        
    def ground_all(self):
        self.write('close (@1!0:24!0)')
        
    def ground_single(self, val):
        # Only grounds channel <val>
        self.write('close (@' + str(val) + '!0)')

    def connect_to_bnc(self, sample_channel, BNC_channel, print_warning=True):
        # Connects Fisher channel <sample_channel> to BNC channel <BNC_channel>
        if sample_channel > 0 and sample_channel < 25 and BNC_channel > 0 and BNC_channel < 9:
            # If the sample channel already has other BNC terminal(s) open to it, print a warning
            if str(sample_channel) + '!' in self.get_closed() and print_warning:
                print(' <!> Another BNC terminal is already connected to the same sample channel.')
            # Make the physical connection
            self.write('close (@' + str(sample_channel) + '!' + str(BNC_channel) + ')')  
            
    def disconnect_from_bnc(self, sample_channel, BNC_channel):
        if sample_channel > 0 and sample_channel < 25 and BNC_channel > 0 and BNC_channel < 9:
            # Break the physical connection
            self.write('open (@' + str(sample_channel) + '!' + str(BNC_channel) + ')')  

    def get_closed(self):
        return self.query('clos:stat?')
    
    def get_status(self):
        # Human-readable version of get_closed.
        print('<> Listing all closed relays')
        resp = self.query('clos:stat?')
        items = resp.split(',')
        for item in items:
            item = item.strip('(@').strip(')')
            if ':' in item:
                # If ':' is in the text, we are dealing with a range
                range_list = item.split(':')
                start_num = range_list[0].split('!')[0]
                group_num = range_list[0].split('!')[1]
                end_num = range_list[1].split('!')[0]
                
                if group_num == '0':
                    print('   Device pins ' + str(start_num).ljust(2) + ' through ' + str(end_num).ljust(2) + ' are connected to the soft-acting ground')
                elif group_num == '9':
                    print('   Device pins ' + str(start_num).ljust(2) + ' through ' + str(end_num).ljust(2) + ' are connected to the corresponding pins on the IN Fisher connector')
                else:
                    print('   Device pins ' + str(start_num).ljust(2) + ' through ' + str(end_num).ljust(2) + ' are connected to BNC terminal' + str(group_num).ljust(2))                
            else:
                # Single connections
                connections = item.split('!')
                if connections[1] == '!0':
                    print('   Device pin ' + str(connections[0]).ljust(2) + ' is connected to the soft-acting ground')
                elif connections[1] == '!9':
                    print('   Device pin ' + str(connections[0]).ljust(2) + ' is connected to the corresponding pin on the IN Fisher connector')
                else:
                    print('   Device pin ' + str(connections[0]).ljust(2) + ' is connected to BNC terminal ' + str(connections[1].strip(')').ljust(2)))


    # Error handling
    def get_error(self):
        """Read single error"""
        return self.query("SYST:ERR?")

    def get_all_errors(self):
        """Read and clear all errors"""
        errors = []
        while True:
            err = self.get_error()
            if err.startswith("0"):
                break
            errors.append(err)
        return errors


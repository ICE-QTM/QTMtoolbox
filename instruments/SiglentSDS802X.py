# -*- coding: utf-8 -*-
"""
Module to interact with a Siglent SDS802X oscilloscope.

Driver based on Siglent manual (broken), ChatGPT debugging (less broken) and debugging.
Current version handles data well up to ~< 10M points, for deeper memory code has to be fixed.
Using fixed mem depth of i.e. 100k points sounds like a reasonable starting point.

"""

import pyvisa as visa
import numpy as np
import struct
from matplotlib import pyplot as plt
import gc
import re
import time

# Variables defined by manual of the oscilloscope
tdiv_enum = [200e-12,500e-12, 1e-9,\
 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, \
 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6, \
 1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, \
 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
HORI_NUM = 10

class WrongInstrErr(Exception):
    pass


class SiglentSDS802X:

    type = 'Siglent SDS802X'

    def __init__(self, address= 'USB0::0xF4EC::0x1017::SDS08A0CA02543::INSTR'):

        rm = visa.ResourceManager()

        # Examples:
        # USB0::0xF4EC::0xEE38::SDS8XXXX::INSTR
        # TCPIP0::192.168.1.100::INSTR

        self.visa = rm.open_resource(address)

        self.visa.timeout = 5000 # 5 seconds
        self.visa.chunk_size = 20 * 1024 * 1024 # default according to manual
        self.visa.read_termination = '\n'
        self.visa.write_termination = '\n'

        resp = self.visa.query('*IDN?')

        if 'SDS8' not in resp:
            raise WrongInstrErr(
                'Expected Siglent SDS800 series, got {}'.format(resp)
            )

    def get_iden(self):
        return str(self.visa.query('*IDN?'))

    def close(self):
        self.visa.close()

    def query(self, val):
        return self.visa.query(val)

    def write(self, val):
        self.visa.write(val)
        
    def reboot(self):
        # Reboot the scope
        self.visa.write('SYST:REBOOT')
        
    def get_error(self):
        return self.query('SYST:ERR?')
    
    def clear(self):
        self.visa.clear()
        
    def reset(self):
        self.visa.write('*RST')

    # --------------------------------------------------
    # Measurements
    # --------------------------------------------------

    def read_meas1(self):
        return float(self.query('MEAD? P1'))

    def read_meas2(self):
        return float(self.query('MEAD? P2'))

    def read_meas3(self):
        return float(self.query('MEAD? P3'))

    def read_meas4(self):
        return float(self.query('MEAD? P4'))

    # --------------------------------------------------
    # Divisions
    # --------------------------------------------------

    def write_horzdiv(self, val):
        self.write('TDIV {}'.format(float(val)))

    def write_vertdiv1(self, val):
        self.write('C1:VDIV {}'.format(float(val)))

    def write_vertdiv2(self, val):
        self.write('C2:VDIV {}'.format(float(val)))

    def read_horzdiv(self):
        return float(self.query('TDIV?').strip('S'))

    def read_vertdiv1(self):
        return float(self.query('C1:VDIV?').split(' ')[1].strip('V'))

    def read_vertdiv2(self):
        return float(self.query('C2:VDIV?').split(' ')[1].strip('V'))
    
    # --------------------------------------------------
    # Acquisition
    # --------------------------------------------------
    
    def read_npoints(self):
        return int(float(self.query('ACQ:POIN?')))
    
    def read_nbits(self):
        return int(self.query('ACQ:RES?').strip('Bits'))
    
    def read_samplingrate(self):
        return int(float(self.query('ACQ:SRAT?')))
    
    def write_samplingrate(self, val):
        if not isinstance(val, int):
            return ValueError('Expected an integer, got: ' + str(type(val)))
        self.write(':ACQ:SRAT ' + str(val))
        
    def read_maxmemdepth(self):
        return self.query('ACQ:MDEP?')
    
    def write_maxmemdepth(self, val):
        # Possible strings: 10M, 1M, 100k, 10k
        self.write(':ACQ:MDEP ' + str(val))
    
    
    # --------------------------------------------------
    # Waveforms
    # --------------------------------------------------

    def select_ch(self, val):
        if not isinstance(val, str):
            # If val is a number, assume one wants an analog channel (C1, C2, ...)
            self.write(':WAV:SOUR C' + str(val))
        else:
            # If val is a string, one might want the Math channel (F1, F2, ...) or a digital channel (D1, D2, ...)
            self.write(':WAV:SOUR ' + val)
             
    # Get main descriptor values for a given channel - taken from Siglent manual (https://siglentna.com/wp-content/uploads/dlm_uploads/2024/09/SDS800XHD_Series_ProgrammingGuide_EN11G.pdf)
    def get_desc(self, ch):
        self.visa.clear()
        self.write('WAV:PRE?')
        recv_all = self.visa.read_raw()
        recv = recv_all[recv_all.find(b'#') + 11:]
        
        param_addr_type={"data_bytes":[0x3c,"i"], # Number of bytes
                         "point_num":[0x74,'i'],  # Number of data points
                         "fp":[0x84,'i'],         # First point. Offset relative to beginning of trace buffer (same as WAV:STAR)
                         "sp":[0x88,'i'],         # Data interval (same as WAV:INT)
                         "vdiv":[0x9c,'f'],
                         "offset":[0xa0,'f'],
                         "code":[0xa4,'f'], 
                         "adc_bit":[0xac,'h'],
                         "interval":[0xb0,'f'],
                         "delay":[0xb4,'d'],
                         "tdiv":[0x144,'h'],
                         "probe":[0x148,'f']}
        data_byte = {"i": 4, "f": 4, "h": 2, "d": 8}
        param_val ={}
        for key,addr_type in param_addr_type.items():
            addr_start = addr_type[0]
            format = addr_type[1]
            bytes = recv[addr_start:addr_start+data_byte[format]]
            param_val[key] = struct.unpack(format, bytes)[0]

        param_val["tdiv"] = tdiv_enum[param_val["tdiv"]]
        param_val["vdiv"] = param_val["vdiv"]*param_val["probe"]
        param_val["offset"] = param_val["offset"]*param_val["probe"]
     
        self.visa.clear()
        return param_val
    
    def get_waveform(self, ch):
        '''
        The waveform generator does not always return the right amount of bytes. In some cases, the device states it's going to send i.e. 1000 bytes
        and hence we would expect 1007 as byte length (incl. header), but when we use self.visa.read_raw() and then get len() of that command, we get something
        less.
        
        Dirty workaround: try a few times to capture the waveform as the dropped packages are occasional. If after 5 trials no data is captured, return
        an error

        '''
        counter = 0
        while counter < 5:
            try:        
                self.write(':WAV:STAR 0')
                time.sleep(0.05)
                
                # Get preamble
                param_dic = self.get_desc(ch)
                          
                # Get the waveform points and confirm the number of waveform slice reads
                points = param_dic["point_num"]
                one_piece_num = float(self.query(":WAVeform:MAXPoint?").strip())
                read_times = int(np.ceil(points / one_piece_num))
                #Set the number of read points per slice, if the waveform points is greater than the maximum number of slice reads
                if points > one_piece_num:
                    self.write(":WAVeform:POINt {}".format(one_piece_num))
                # Choose the format of the data returned
                self.write(":WAVeform:WIDTh BYTE")
                if param_dic['adc_bit'] > 8:
                    self.write(":WAVeform:WIDTh WORD")
                #Get the waveform data for each slice
                recv_byte = b''
                for i in range(0, read_times):
                    # Always clear visa before retrieving data
                    self.visa.clear()
                    
                    start = i * one_piece_num
                    #Set the starting point of each slice
                    self.write(":WAVeform:STARt {}".format(start))
                    #Get the waveform data of each slice
                    self.write("WAV:DATA?")
                    time.sleep(0.05)
                    recv_rtn = self.visa.read_raw()
        
                    #Splice each waveform data based on data block information
                    block_start = recv_rtn.find(b'#')
                    
                    if block_start < 0:
                        break
        
                    data_digit = int(recv_rtn[block_start + 1:block_start + 2])
                    data_start = block_start + 2 + data_digit
                    data_len = int(recv_rtn[block_start + 2:data_start])
                    recv_byte += recv_rtn[data_start:data_start + data_len]
                                
                # Unpack signed byte data.
                if param_dic['adc_bit'] > 8:
                    convert_data = np.array(struct.unpack("%dh"%points, recv_byte))
                else:
                    convert_data = np.array(struct.unpack("%db"%points, recv_byte))
                                          
                del recv_byte
                gc.collect()
                #Calculate the voltage value and time value
                volt_value = (
                    convert_data /
                    param_dic["code"] *
                    param_dic["vdiv"] -
                    param_dic["offset"]
                )
                
                time_value = (
                    -(param_dic['tdiv'] * HORI_NUM / 2)
                    + np.arange(len(convert_data)) *
                      param_dic['interval']
                    + param_dic['delay']
                )
        
                counter = 5 # Breaks the loop immediately
            
            except Exception:
                counter += 1
                print('Something went wrong. Trying to get waveform again... (Attempts done: ' + str(counter) + ')')
                pass
            
        return time_value, volt_value
            
    def get_waveform_v2(self, ch):
        '''
        New version: assume that waveform is always transferred in single block. Check for correct amount of bytes during transfer,
        try to get rest of bytes in successive call if needed

        '''      
        self.write(':WAV:STAR 0')
        time.sleep(0.05)
        self.write(':WAV:WIDT WORD')
        time.sleep(0.05)

        # Get preamble
        param_dic = self.get_desc(ch)
                  
        # Get the waveform points and confirm the number of waveform slice reads
        points = param_dic["point_num"]
        
        # The length of the binary data that we expect to retrieve is 2 * points plus a header. The header length we can get from the binary string itself.
        expected_byte_length = 1 * points # for BYTE width
        
        # Choose the format of the data returned
        self.write(":WAVeform:WIDTh BYTE")
        if param_dic['adc_bit'] > 8:
            self.write(":WAVeform:WIDTh WORD")
            expected_byte_length = 2 * points # for WORD width
        #Get the waveform data for each slice
        recv_byte = b''

        #Get the waveform data of each slice
        self.write("WAV:DATA?")
        time.sleep(0.05)
        # Receive data bytes
        data_bytes = b''
        header_length = -9999
        
        got_all_data = False
        while not got_all_data: 
            # Receive a block of data, add to data_bytes
            recv_rtn = self.visa.read_raw()
            
            if len(data_bytes) == 0:
                # Extract header:
                if recv_rtn[0:1] != b'#':
                    raise ValueError('Not a SCPI block, got: ' + repr(recv_rtn[:20]))
                    
                N = int(chr(recv_rtn[1]))
                header_length = 3 + N 
            
            # Concatenate the data streams
            data_bytes = data_bytes + recv_rtn
            # Check for total length of data bytes
            data_length = len(data_bytes)
                
            # Only continue if full payload has been delivered
            if data_length - header_length == expected_byte_length:
                got_all_data = True
            else:
                print('Error in getting all data, retrying...')

        #Splice each waveform data based on data block information
        block_start = 0

        data_digit = int(recv_rtn[block_start + 1:block_start + 2])
        data_start = block_start + 2 + data_digit
        data_len = int(recv_rtn[block_start + 2:data_start])
        recv_byte += recv_rtn[data_start:data_start + data_len]
                        
        # Unpack signed byte data.
        if param_dic['adc_bit'] > 8:
            convert_data = np.array(struct.unpack("%dh"%points, recv_byte))
        else:
            convert_data = np.array(struct.unpack("%db"%points, recv_byte))
                                  
        del recv_byte
        gc.collect()
        #Calculate the voltage value and time value
        volt_value = (
            convert_data /
            param_dic["code"] *
            param_dic["vdiv"] -
            param_dic["offset"]
        )
        
        time_value = (
            -(param_dic['tdiv'] * HORI_NUM / 2)
            + np.arange(len(convert_data)) *
              param_dic['interval']
            + param_dic['delay']
        )
 
        print('Waveform captured!')
          

        


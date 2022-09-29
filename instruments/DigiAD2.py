# -*- coding: utf-8 -*-
"""
Module to interact with a Digilent Analog Discovery 2.
Uses the WaveForms SDK to communicate to the USB device.

Version 0.1 (2022-09-29)
Daan Wielens - Researcher at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import numpy as np
import ctypes
from sys import path

# Load the dynamic library of the Waveform SDK
dwf = ctypes.cdll.dwf
constants_path = r"C:\Program Files (x86)\Digilent\WaveFormsSDK\samples\py"
path.append(constants_path)
import dwfconstants as constants

class DigiAD2:
    type = 'Digilent Analog Discovery 2'
    
    def __init__(self, config=0):
        '''Initialize connection to the device'''
        self.handle = ctypes.c_int()
        self.config = config
        dwf.FDwfDeviceConfigOpen(ctypes.c_int(-1), ctypes.c_int(self.config), ctypes.byref(self.handle))
        # Config 0 : Scope 8k  , Wavegen 4k
        # Config 1 : Scope 16k , Wavegen 1k
        
    def close(self):
        '''Close connection to the device'''
        dwf.FDwfDeviceClose(self.handle)
        self.handle = ctypes.c_int(0)
        
        
    def open_scope(self, freq=20E6, npoints=8192, offset=0, amp_range=5):
        '''
        Initialize connection to the scope, write acquisition settings
        Parameters: - freq:      sampling frequency in Hz, default = 20 MHz
                    - npoints:   number of points, default = 8192
                    - offset:    offset voltage in V, default = 0 V
                    - amp_range: amplitude range in V, default = +/- 5 V
        '''
        # Enable all channels
        dwf.FDwfAnalogInChannelEnableSet(self.handle, ctypes.c_int(0), ctypes.c_bool(True))
   
        # Set offset voltage (in Volts)
        dwf.FDwfAnalogInChannelOffsetSet(self.handle, ctypes.c_int(0), ctypes.c_double(offset))
     
        # Set range (maximum signal amplitude in Volts)
        dwf.FDwfAnalogInChannelRangeSet(self.handle, ctypes.c_int(0), ctypes.c_double(amp_range))
     
        # Set the buffer size (data point in a recording)
        dwf.FDwfAnalogInBufferSizeSet(self.handle, ctypes.c_int(int(npoints)))
     
        # Set the acquisition frequency (in Hz)
        dwf.FDwfAnalogInFrequencySet(self.handle, ctypes.c_double(freq))
     
        # Disable averaging (for more info check the documentation)
        dwf.FDwfAnalogInChannelFilterSet(self.handle, ctypes.c_int(-1), constants.filterDecimate)
        self.freq = freq
        self.buffer = int(npoints)
        
    def close_scope(self):
        '''Reset the scope'''
        dwf.FDwfAnalogInReset(self.handle)
        
    def read_volt1(self):
        '''Measure the voltage of channel 1'''
        # Set up the instrument
        dwf.FDwfAnalogInConfigure(self.handle, ctypes.c_bool(False), ctypes.c_bool(False))     
        # Read data to an internal buffer
        dwf.FDwfAnalogInStatus(self.handle, ctypes.c_bool(False), ctypes.c_int(0))     
        # Extract data from that buffer
        voltage = ctypes.c_double()   # variable to store the measured voltage
        dwf.FDwfAnalogInStatusSample(self.handle, ctypes.c_int(0), ctypes.byref(voltage))     
        # Store the result as float
        voltage = voltage.value
        return voltage
        
    def read_volt2(self):
        '''Measure the voltage of channel 2'''
        # Set up the instrument
        dwf.FDwfAnalogInConfigure(self.handle, ctypes.c_bool(False), ctypes.c_bool(False))     
        # Read data to an internal buffer
        dwf.FDwfAnalogInStatus(self.handle, ctypes.c_bool(False), ctypes.c_int(0))     
        # Extract data from that buffer
        voltage = ctypes.c_double()   # variable to store the measured voltage
        dwf.FDwfAnalogInStatusSample(self.handle, ctypes.c_int(1), ctypes.byref(voltage))     
        # Store the result as float
        voltage = voltage.value
        return voltage    

    def get_wav1(self):
        """
        Record V(t) for a number of 'npoints' (as defined in open_scope)
        Returns: - time :    list of timestamps in s
                 - voltages: list of voltages in V
        """
        # set up the instrument
        dwf.FDwfAnalogInConfigure(self.handle, ctypes.c_bool(False), ctypes.c_bool(True))
     
        # read data to an internal buffer
        while True:
            status = ctypes.c_byte()    # variable to store buffer status
            dwf.FDwfAnalogInStatus(self.handle, ctypes.c_bool(True), ctypes.byref(status))
     
            # check internal buffer status
            if status.value == constants.DwfStateDone.value:
                    # exit loop when ready
                    break
     
        # copy buffer
        buffer = (ctypes.c_double * self.buffer)()   # create an empty buffer
        dwf.FDwfAnalogInStatusData(self.handle, ctypes.c_int(0), buffer, ctypes.c_int(self.buffer))
     
        # calculate aquisition time
        time = range(0, self.buffer)
        time = [moment / self.freq for moment in time]
     
        # convert into list
        voltages = [float(element) for element in buffer]
        return time, voltages
    
    def get_wav2(self):
        """
        Record V(t) for a number of 'npoints' (as defined in open_scope)
        Returns: - time :    list of timestamps in s
                 - voltages: list of voltages in V
        """
        # set up the instrument
        dwf.FDwfAnalogInConfigure(self.handle, ctypes.c_bool(False), ctypes.c_bool(True))
     
        # read data to an internal buffer
        while True:
            status = ctypes.c_byte()    # variable to store buffer status
            dwf.FDwfAnalogInStatus(self.handle, ctypes.c_bool(True), ctypes.byref(status))
     
            # check internal buffer status
            if status.value == constants.DwfStateDone.value:
                    # exit loop when ready
                    break
     
        # copy buffer
        buffer = (ctypes.c_double * self.buffer)()   # create an empty buffer
        dwf.FDwfAnalogInStatusData(self.handle, ctypes.c_int(1), buffer, ctypes.c_int(self.buffer))
     
        # calculate aquisition time
        time = range(0, self.buffer)
        time = [moment / self.freq for moment in time]
     
        # convert into list
        voltages = [float(element) for element in buffer]
        return time, voltages

    def trigger(self, enable=True, source='analog', channel=0, timeout=0, edge_rising=True, level=0):
        '''
        Set up triggering for the scope
        Parameters: - enable trigger?: bool
                    - trigger source: none, analog, digital, external[1-4]
                    - trigger channel: 1-4 for analog, 0-15 for digital
                    - timeout: seconds (default = 0)
                    - trigger edge rising: true = rising, false = falling (default rising)
                    - trigger level: volts (default = 0)                   
        '''
        # Translate options to constants
        if source == 'none':
            source = constants.trigsrcNone
        elif source == 'analog':
            source = constants.trigsrcDetectorAnalogIn
        elif source == 'digital':
            source = constants.trigsrcDetectorDigitalIn
        else:
            raise ValueError('This has not been implemented yet, sorry.')
            
        if enable and source != constants.trigsrcNone:
            # enable/disable auto triggering
            dwf.FDwfAnalogInTriggerAutoTimeoutSet(self.handle, ctypes.c_double(timeout))
        
            # set trigger source
            dwf.FDwfAnalogInTriggerSourceSet(self.handle, source)
        
            # set trigger channel
            if source == constants.trigsrcDetectorAnalogIn:
                channel -= 1    # decrement analog channel index
            dwf.FDwfAnalogInTriggerChannelSet(self.handle, ctypes.c_int(channel))
        
            # set trigger type
            dwf.FDwfAnalogInTriggerTypeSet(self.handle, constants.trigtypeEdge)
        
            # set trigger level
            dwf.FDwfAnalogInTriggerLevelSet(self.handle, ctypes.c_double(level))
        
            # set trigger edge
            if edge_rising == True:
                # rising edge
                dwf.FDwfAnalogInTriggerConditionSet(self.handle, constants.trigcondRisingPositive)
            elif edge_rising == False:
                # falling edge
                dwf.FDwfAnalogInTriggerConditionSet(self.handle, constants.trigcondFallingNegative)
            self.triggering = True
        else:
            # turn off the trigger
            dwf.FDwfAnalogInTriggerSourceSet(self.handle, constants.trigsrcNone)
            self.triggering = False
        return
    
    def set_wav1(self, function, frequency=1e03, amplitude=1, offset=0, symmetry=50, wait=0, run_time=0, repeat=0, data=[]):
        """
            generate an analog signal
            parameters: - device data
                        - function - possible: custom, sine, square, triangle, noise, ds, pulse, trapezium, sine_power, ramp_up, ramp_down
                        - frequency in Hz, default is 1KHz
                        - amplitude in Volts, default is 1V
                        - offset voltage in Volts
                        - signal symmetry in percentage, default is 50%
                        - wait time in seconds, default is 0s
                        - run time in seconds, default is infinite (0)
                        - repeat count, default is infinite (0)
                        - data - list of voltages, used only if function=custom, default is empty
        """
        if function == 'custom':
            function = constants.funcCustom
        elif function == 'sine':
            function = constants.funcSine
        elif function == 'square':
            function = constants.funcSquare
        elif function == 'triangle':
            function = constants.funcTriangle
        elif function == 'noise':
            function = constants.funcNoise
        elif function == 'dc':
            function = constants.funcDC
        elif function == 'pulse':
            function = constants.funcPulse
        elif function == 'trapezium':
            function = constants.funcTrapezium
        elif function == 'sine_power':
            function = constants.funcSinePower
        elif function == 'ramp_up':
            function = constants.funcRampUp
        elif function == 'ramp_down':
            function = constants.funcRampDn
        else:
            print('Warning. We will try to pass along your function directly.')
      
        # enable channel
        channel = ctypes.c_int(0)
        dwf.FDwfAnalogOutNodeEnableSet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_bool(True))
     
        # set function type
        dwf.FDwfAnalogOutNodeFunctionSet(self.handle, channel, constants.AnalogOutNodeCarrier, function)
     
        # load data if the function type is custom
        if function == constants.funcCustom:
            data_length = len(data)
            buffer = (ctypes.c_double * data_length)()
            for index in range(0, len(buffer)):
                buffer[index] = ctypes.c_double(data[index])
            dwf.FDwfAnalogOutNodeDataSet(self.handle, channel, constants.AnalogOutNodeCarrier, buffer, ctypes.c_int(data_length))
     
        # set frequency
        dwf.FDwfAnalogOutNodeFrequencySet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(frequency))
     
        # set amplitude or DC voltage
        dwf.FDwfAnalogOutNodeAmplitudeSet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(amplitude))
     
        # set offset
        dwf.FDwfAnalogOutNodeOffsetSet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(offset))
     
        # set symmetry
        dwf.FDwfAnalogOutNodeSymmetrySet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(symmetry))
     
        # set running time limit
        dwf.FDwfAnalogOutRunSet(self.handle, channel, ctypes.c_double(run_time))
     
        # set wait time before start
        dwf.FDwfAnalogOutWaitSet(self.handle, channel, ctypes.c_double(wait))
     
        # set number of repeating cycles
        dwf.FDwfAnalogOutRepeatSet(self.handle, channel, ctypes.c_int(repeat))
     
        # start
        dwf.FDwfAnalogOutConfigure(self.handle, channel, ctypes.c_bool(True))

    def set_wav2(self, function, frequency=1e03, amplitude=1, offset=0, symmetry=50, wait=0, run_time=0, repeat=0, data=[]):
        """
            generate an analog signal
            parameters: - device data
                        - function - possible: custom, sine, square, triangle, noise, ds, pulse, trapezium, sine_power, ramp_up, ramp_down
                        - frequency in Hz, default is 1KHz
                        - amplitude in Volts, default is 1V
                        - offset voltage in Volts
                        - signal symmetry in percentage, default is 50%
                        - wait time in seconds, default is 0s
                        - run time in seconds, default is infinite (0)
                        - repeat count, default is infinite (0)
                        - data - list of voltages, used only if function=custom, default is empty
        """
        if function == 'custom':
            function = constants.funcCustom
        elif function == 'sine':
            function = constants.funcSine
        elif function == 'square':
            function = constants.funcSquare
        elif function == 'triangle':
            function = constants.funcTriangle
        elif function == 'noise':
            function = constants.funcNoise
        elif function == 'dc':
            function = constants.funcDC
        elif function == 'pulse':
            function = constants.funcPulse
        elif function == 'trapezium':
            function = constants.funcTrapezium
        elif function == 'sine_power':
            function = constants.funcSinePower
        elif function == 'ramp_up':
            function = constants.funcRampUp
        elif function == 'ramp_down':
            function = constants.funcRampDn
        else:
            print('Warning. We will try to pass along your function directly.')
      
        # enable channel
        channel = ctypes.c_int(1)
        dwf.FDwfAnalogOutNodeEnableSet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_bool(True))
     
        # set function type
        dwf.FDwfAnalogOutNodeFunctionSet(self.handle, channel, constants.AnalogOutNodeCarrier, function)
     
        # load data if the function type is custom
        if function == constants.funcCustom:
            data_length = len(data)
            buffer = (ctypes.c_double * data_length)()
            for index in range(0, len(buffer)):
                buffer[index] = ctypes.c_double(data[index])
            dwf.FDwfAnalogOutNodeDataSet(self.handle, channel, constants.AnalogOutNodeCarrier, buffer, ctypes.c_int(data_length))
     
        # set frequency
        dwf.FDwfAnalogOutNodeFrequencySet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(frequency))
     
        # set amplitude or DC voltage
        dwf.FDwfAnalogOutNodeAmplitudeSet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(amplitude))
     
        # set offset
        dwf.FDwfAnalogOutNodeOffsetSet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(offset))
     
        # set symmetry
        dwf.FDwfAnalogOutNodeSymmetrySet(self.handle, channel, constants.AnalogOutNodeCarrier, ctypes.c_double(symmetry))
     
        # set running time limit
        dwf.FDwfAnalogOutRunSet(self.handle, channel, ctypes.c_double(run_time))
     
        # set wait time before start
        dwf.FDwfAnalogOutWaitSet(self.handle, channel, ctypes.c_double(wait))
     
        # set number of repeating cycles
        dwf.FDwfAnalogOutRepeatSet(self.handle, channel, ctypes.c_int(repeat))
     
        # start
        dwf.FDwfAnalogOutConfigure(self.handle, channel, ctypes.c_bool(True))
        
    def close_wav1(self):
        dwf.FDwfAnalogOutReset(self.handle, ctypes.c_int(0))

    def close_wav2(self):
        dwf.FDwfAnalogOutReset(self.handle, ctypes.c_int(1))
                
    def get_version(self):
        version = ctypes.create_string_buffer(16)
        dwf.FDwfGetVersion(version)
        return str(version.value)[2:-1]
    
    def get_trig_slope(self):
        resp = ctypes.c_int()
        dwf.FDwfDeviceTriggerSlopeInfo(self.handle, resp)
        return resp.value
    
    def get_trig(self):
        resp = ctypes.c_int()
        dwf.FDwfAnalogInTriggerConditionInfo(self.handle, resp)
        return resp.value
    
    def set_trig_type(self, trig_type=0):
        dwf.FDwfAnalogInTriggerConditionSet(self.handle, ctypes.c_int(trig_type))
        
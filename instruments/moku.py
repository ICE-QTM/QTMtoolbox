# -*- coding: utf-8 -*-
"""
Module to interact with Moku devices (tested on Go, Pro).
Uses the Moku API to communicate with the device.

Version 0.1 (2024-01-15)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl

-----------------------------------------------------------
The Moku equipment requires additional software to be installed:
1. Install the desktop app from https://www.liquidinstruments.com/products/desktop-apps/
2. In Python, install the Moku package via 'pip install moku'
3. Download the required moku files in a command prompt (Anaconda Prompt) via 'moku download'. 
   To make sure that the correct files are downloaded, use 'moku download --fw_ver=<version>', where the 
   <version> is an integer that can be obtained by running the desktop software and right-clicking the Moku
   device to get the firmware version.
-----------------------------------------------------------
"""

from moku.instruments import MultiInstrument
from moku.instruments import Oscilloscope
from moku.instruments import WaveformGenerator
import numpy as np

class moku:
    type = 'Moku'
    
    def __init__(self, IPaddress, moku_type = 'Pro'):
        '''
        Upon initialization, the Moku's firmware is overwritten and any existing connection to the device is forced to close.
        This wrapper will initialize the Moku into the MultiInstrument mode.

        Parameters
        ----------
        IPaddress : String
            The IP address of the Moku device. The address includes square brackets. Example: '[fe80::xxxx:xxxx:xxx:xxx]'
        moku_type : String, optional
            Type of Moku device that is used. The default is 'Pro', valid options can be 'Go', 'Lab', 'Pro'.

        Returns
        -------
        None.

        '''
        if moku_type == 'Pro':
            self.mim = MultiInstrument(IPaddress, force_connect = True, platform_id = 4)
            self.moku_type = 'Pro'
        elif moku_type == 'Go':
            self.mim = MultiInstrument(IPaddress, force_connect = True, platform_id = 2)
            self.moku_type = 'Go'
        elif moku_type == 'Lab':
            self.mim = MultiInstrument(IPaddress, force_connect = True, platform_id = 2)
            self.moku_type = 'Lab'
        else:
            raise ValueError('No valid Moku type is provided. moku_type can be "Go", "Lab", "Pro".')
            
    def single_wg_osc_init(self, input_impedance='1MOhm', input_coupling='DC', input_attenuation='0dB', output_gain='0dB'):
        '''
        This function creates two software instruments: a waveform generator on slot1, and an oscilloscope on slot2. 
        Input-output routing is as follows:
            
            Waveform generator output A ---> Output 1
                                         |-> Oscilloscope input A
                                         
                                Input 1 ---> Oscilloscope input B

        Parameters
        ----------
        input_impedance : String, optional
            Sets the impedance of the input channels. Options are '50Ohm' or '1MOhm'. The default is '1MOhm'. Note that the Moku:Go only can use '1MOhm', so if moku_type is Go, the input_impedance will be omitted.
        input_coupling : String, optional
            Sets the coupling of the input channels. Options are 'DC' or 'AC'. The default is 'DC'.
        input_attenuation : String, optional
            Sets the attenuation of the input channels. The default is '0dB'. Options vary per device type. Moku:Go can use '0dB', '-14dB'. Moku:Lab can use '0dB', '-20dB'. Moku:Pro can use '0dB', '-20dB', '-40dB'.
        output_gain : String, optional
            Sets the gain of the output channel. Options are '0dB', '14dB'. The default is '0dB'.

        Returns
        -------
        None.

        '''
        # Create devices (flash FPGA)
        self.wg = self.mim.set_instrument(1, WaveformGenerator)
        self.osc = self.mim.set_instrument(2, Oscilloscope)
        
        # Write connection list
        connections = [dict(source='Input1', destination='Slot2InB'), # Physical input 1 to Slot 2 (scope) software input B
                       dict(source='Slot1OutA', destination='Slot2InA'), # Waveform software output A to scope software input A
                       dict(source='Slot1OutA', destination='Output1')]  # Waveform software output A to physical output 1
        self.mim.set_connections(connections=connections)
        
        #Configure inputs
        if self.moku_type == 'Pro':
            if input_attenuation in ['0dB', '-20dB', '-40dB']: 
                self.mim.set_frontend(1, input_impedance, input_coupling, input_attenuation)
        if self.moku_type == 'Go':
            if input_attenuation in ['0dB', '-14dB']:
                self.mim.set_frontend(1, '1MOhm', input_coupling, input_attenuation)
        if self.moku_type == 'Lab':
            if input_attenuation in ['0dB', '-20dB']: 
                self.mim.set_frontend(1, input_impedance, input_coupling, input_attenuation) 
                
        # Configure outputs
        self.mim.set_output(1, output_gain)
        
    def single_wg_osc_set_wg(self, wg_type='Sine', wg_amplitude=4e-3, wg_frequency=1000, wg_offset=0, wg_phase=0, wg_symmetry=50, wg_square_duty=0, wg_dc_level=0, wg_pulse_edge_time=0, wg_pulse_width=0, wg_termination='50Ohm'):
        '''
        This function configures the waveform generator by setting up a waveform and, if applicable, selecting the output termination mode.

        Parameters
        ----------
        wg_type : String, optional
            Options are: 'Off', 'Sine', 'Square', 'Ramp', 'Pulse', 'DC', 'Noise'. The default is 'Sine'.
        wg_amplitude : float, optional
            Waveform peak-to-peak amplitude in V. The default is 4e-3. Range is 4e-3 to 10 V (depending on output gain)
        wg_frequency : float, optional
            Waveform frequency in Hz. The default is 1000.
        wg_offset : float, optional
            Waveform offset in V. The default is 0.
        wg_phase : float, optional
            Waveform phase offset in degrees. The default is 0.
        wg_symmetry : float, optional
            Fraction of the cycle rising in %. The default is 50.
        wg_square_duty : float, optional
            Square wave duty cycle %. The default is 0. This option only works for square type
        wg_dc_level : float, optional
            DC output level in V. The default is 0. This argurment only works for DC type
        wg_pulse_edge_time : float, optional
            Edge-time of the waveform. The default is 0. This argument only works for pulse type
        wg_pulse_width : float, optional
            Pulse width of the waveform. The default is 0. This argument only works for pulse type
        wg_termination : String, optional
            Select the output termination mode. Options are '50Ohm' or 'HiZ'. The default is '50Ohm'. This argument does not apply to Moku:Go device types.

        Returns
        -------
        None.

        '''
        
        # Only the Moku:Pro and Moku:Lab support output_termination changes, so for Moku:Go ignore whatever is selected
        if self.moku_type != 'Go':
            self.wg.set_output_termination(wg_termination)
        
        # If wg_amplitude == 0, simply set the wg_type to Off to achieve this value.
        if wg_amplitude == 0:
            self.wg.generate_waveform(channel=1, type='Off')
        
        # Waveforms with standard attributes
        elif wg_type not in ['Pulse', 'DC', 'Square']:
            self.wg.generate_waveform(channel=1, type=wg_type, amplitude=wg_amplitude, frequency=wg_frequency, offset=wg_offset, phase=wg_phase, symmetry=wg_symmetry)
            
        elif wg_type == 'Pulse':
            self.wg.generate_waveform(channel=1, type=wg_type, amplitude=wg_amplitude, frequency=wg_frequency, offset=wg_offset, phase=wg_phase, symmetry=wg_symmetry, edge_time=wg_pulse_edge_time, pulse_width=wg_pulse_width)   
            
        elif wg_type == 'DC':
            self.wg.generate_waveform(channel=1, type=wg_type, dc_level=wg_dc_level)
            
        elif wg_type == 'Square':
            self.wg.generate_waveform(channel=1, type=wg_type, amplitude=wg_amplitude, frequency=wg_frequency, offset=wg_offset, phase=wg_phase, symmetry=wg_symmetry, duty=wg_square_duty)
            
    def single_wg_osc_set_osc(self, t1=0, t2=1, trigger_source='ChannelA', edge='Rising', level=0, acquisition_mode='Precision', npoints=4096):
        '''
        This function configures the parameters of the oscilloscope.

        Parameters
        ----------
        t1 : float, optional
            Time from the trigger to the left of the screen, in seconds. The default is 0.
        t2 : float, optional
            Time from the trigger to the right of the screen. t2 must be positive. The default is 1.
        trigger_source : String, optional
            Channel used for triggering. The default is 'Output1'.
        edge : String, optional
            Trigger edge for edge triggering. Options are 'Rising', 'Falling', 'Both'. The default is 'Rising'.
        level : float, optional
            Trigger level in V. The default is 0.
        acquisition_mode : String, optional
            Sets the acquisition mode. Options are 'Normal', 'Precision', 'PeakDetect', 'DeepMemory'. The default is 'Precision'.
        npoints : int, optional
            Number of data points that will be acquired. Should be 2^n, where n >= 7 (256 points) and n <= 14 (16384 points). The default is 4096.

        Returns
        -------
        None.

        '''
        
        self.osc.osc_measurement(t1=t1, t2=t2, trigger_source=trigger_source, edge=edge, level=level) 
        self.osc.set_acquisition_mode(acquisition_mode)
        # Number of points needs to be 2^n where n is in between 7 (128 points) and 14 (16384 points). If the given 'npoints' is not 2^n with integer n, round to nearest (larger) n.
        npoints = 2**int(np.ceil(np.log(npoints)/np.log(2)))
        self.osc.set_timebase(t1=t1, t2=t2, frame_length=npoints)  
        
    def single_wg_osc_get_wav_navg(self, n_avg=16):
        '''
        This function retrieves waveforms from the oscilloscope. It takes n_avg samples and then averages these to improve SNR.

        Parameters
        ----------
        n_avg : int, optional
            Number of curves that will be taken for averaging. The default is 16.

        Returns
        -------
        V1 : np.array of float
            Voltages of the first channel of the oscilloscope (Waveform generator output A).
        V2 : np.array of float
            Voltages of the second channel of the oscilloscope (Input 1).

        '''
        V1_list = np.array([], dtype=np.float64)
        V2_list = np.array([], dtype=np.float64)
        for i in range(n_avg):
            data = self.osc.get_data()
            print(np.count_nonzero(data['ch1']))
            if len(V1_list) == 0:
                V1_list = data['ch1']
                V2_list = data['ch2']
            else:
                V1_list = np.vstack((V1_list, data['ch1']))
                V2_list = np.vstack((V2_list, data['ch2']))
        if n_avg > 1:
            V1 = np.mean(V1_list, 0)
            V2 = np.mean(V2_list, 0)
            return V1, V2
        else:
            return V1_list, V2_list
    
    def get_moku_data(self):
        return self.osc.get_data()
    
    def close(self):
        self.mim.relinquish_ownership()

# -*- coding: utf-8 -*-
"""
Module to interact with a PXI-5922 Oscilloscope.
Requirements:
- NI PXI Platform Services
- NI-SCOPE software
- Python module nimi-python

Version 1.0 (2022-04-07)
Daan Wielens - Researcher at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import niscope
import numpy as np

class NIpxi5922:
    type = 'NIpxi5922'
    
    def __init__(self, PXIaddr='Dev5'):
        self.PXIaddr = PXIaddr
        
    def get_wav_now(self, fs, npts):
        '''
        Get immediate readings from the PXI-5922 digitizer without triggering.

        Parameters
        ----------
        fs : Int
            The sampling frequency in Hz.
        npts : Int
            The number of points that should be returned.

        Returns
        -------
        CH0 : Array of float64
            Voltages corresponding to Channel 0 of the module.
        CH1 : Array of float64
            Voltages corresponding to Channel 1 of the module.

        '''
        # Inputs must be integers
        fs = int(fs)
        npts = int(npts)
        # Open session only in function definition, so that scope is only 'locked' during acquisition (afterwards, NI InstrumentStudio / Soft Front Panel can take over)
        with niscope.Session(self.PXIaddr) as session:
            # Configure channels
            session.channels[0].configure_vertical(range=1.0, coupling=niscope.VerticalCoupling.DC)
            session.channels[1].configure_vertical(range=1.0, coupling=niscope.VerticalCoupling.DC)
            # Configure horizontal
            session.configure_horizontal_timing(min_sample_rate=fs, min_num_pts=npts, ref_position=0, num_records=1, enforce_realtime=True)     
            # Set up trigger
            session.configure_trigger_edge('0', 0, niscope.TriggerCoupling.DC, niscope.TriggerSlope.POSITIVE)
            with session.initiate():
                waveform = np.ndarray(npts*2, dtype=np.float64)
                session.channels[0,1].fetch_into(waveform, timeout=5.0)
                CH0 = waveform[:npts]
                CH1 = waveform[npts:]            
        return CH0, CH1   
    
    def get_wav_trig(self, fs, npts, channel='0', trigger_level=0, trigger_coupling=niscope.TriggerCoupling.DC, trigger_slope=niscope.TriggerSlope.POSITIVE):
        '''
        Get triggered (edge type) readings from the PXI-5922 digitizer.

        Parameters
        ----------
        fs : Int
            The sampling frequency in Hz.
        npts : Int
            The number of points that should be returned.
        channel : Str
            The channel to trigger on ('0', '1', 'TRIG')
        trigger_level : Float
            The voltage threshold for the trigger.
        trigger_coupling : niscope.TriggerCoupling type
            The trigger coupling. Normally set to niscope.TriggerCoupling.DC
        trigger_slope : niscope.TriggerSlope type
            Specifies whether a rising or falling edge should be used. Normally set to niscope.TriggerSlope.POSITIVE

        Returns
        -------
        CH0 : TYPE
            Array of float64 voltage values, corresponding to Channel 0 of the module.
        CH1 : TYPE
            Array of float64 voltage values, corresponding to Channel 1 of the module.

        '''
        # Inputs must be integers
        fs = int(fs)
        npts = int(npts)
        # Open session only in function definition, so that scope is only 'locked' during acquisition (afterwards, NI InstrumentStudio / Soft Front Panel can take over)
        with niscope.Session(self.PXIaddr) as session:
            # Configure channels
            session.channels[0].configure_vertical(range=1.0, coupling=niscope.VerticalCoupling.DC)
            session.channels[1].configure_vertical(range=1.0, coupling=niscope.VerticalCoupling.DC)
            # Configure horizontal
            session.configure_horizontal_timing(min_sample_rate=fs, min_num_pts=npts, ref_position=0, num_records=1, enforce_realtime=True)     
            # Set up trigger
            session.configure_trigger_edge(channel, trigger_level, trigger_coupling, trigger_slope)
            with session.initiate():
                waveform = np.ndarray(npts*2, dtype=np.float64)
                session.channels[0,1].fetch_into(waveform, timeout=5.0)
                CH0 = waveform[:npts]
                CH1 = waveform[npts:]            
        return CH0, CH1 
    
    def get_wav_trig_avg(self, fs, npts, navg, channel='0', trigger_level=0, trigger_coupling=niscope.TriggerCoupling.DC, trigger_slope=niscope.TriggerSlope.POSITIVE):
        '''
        Get triggered (edge type) readings from the PXI-5922 digitizer. The data
        is collected <navg> times and a np.mean of the data is then returned.
        
        (This is a workaround to get averaging functionality)

        Parameters
        ----------
        fs : Int
            The sampling frequency in Hz.
        npts : Int
            The number of points that should be returned.
        navg : Int
            The number of averages that should be collected before returning the data
        channel : Str
            The channel to trigger on ('0', '1', 'TRIG')
        trigger_level : Float
            The voltage threshold for the trigger.
        trigger_coupling : niscope.TriggerCoupling type
            The trigger coupling. Normally set to niscope.TriggerCoupling.DC
        trigger_slope : niscope.TriggerSlope type
            Specifies whether a rising or falling edge should be used. Normally set to niscope.TriggerSlope.POSITIVE

        Returns
        -------
        CH0 : TYPE
            Array of float64 voltage values, corresponding to Channel 0 of the module.
        CH1 : TYPE
            Array of float64 voltage values, corresponding to Channel 1 of the module.

        '''
        # Inputs must be integers
        fs = int(fs)
        npts = int(npts)
        # Open session only in function definition, so that scope is only 'locked' during acquisition (afterwards, NI InstrumentStudio / Soft Front Panel can take over)
        with niscope.Session(self.PXIaddr) as session:
            # Configure channels
            session.channels[0].configure_vertical(range=1.0, coupling=niscope.VerticalCoupling.DC)
            session.channels[1].configure_vertical(range=1.0, coupling=niscope.VerticalCoupling.DC)
            # Configure horizontal
            session.configure_horizontal_timing(min_sample_rate=fs, min_num_pts=npts, ref_position=0, num_records=1, enforce_realtime=True)     
            # Set up trigger
            session.configure_trigger_edge(channel, trigger_level, trigger_coupling, trigger_slope)
            CH0_list = np.array([], dtype=np.float64)
            CH1_list = np.array([], dtype=np.float64)
            for i in range(navg):
                with session.initiate():
                    waveform = np.ndarray(npts*2, dtype=np.float64)
                    session.channels[0,1].fetch_into(waveform, timeout=5.0)
                    if len(CH0_list) == 0:
                        CH0_list = waveform[:npts]
                        CH1_list = waveform[npts:]
                    else:
                        CH0_list = np.vstack((CH0_list, waveform[:npts]))
                        CH1_list = np.vstack((CH1_list, waveform[npts:]))           
        
        CH0 = np.mean(CH0_list, 0)
        CH1 = np.mean(CH1_list, 0)
        return CH0, CH1
    
# -*- coding: utf-8 -*-
"""
Functions to capture oscilloscope data. The curves are saved into a single
file within the 'ScopeData' directory.

Version 1.0 (2018-10-11)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import visa
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt
import time
import os

def getScope(filename, GPIBaddr=1):
    # Connect to device
    rm = visa.ResourceManager()
    tek = rm.open_resource('GPIB0::{}::INSTR'.format(GPIBaddr))

    #%% Channel 1
    # Prepare scope for acquisition
    tek.write('DATA:SOU CH1')
    tek.write('DATA:WIDTH 1')
    tek.write('DATA:ENC RPB')

    # Get horz/vert settings from scope
    ymult = float(tek.query('WFMPRE:YMULT?')[9:-1])
    yzero = float(tek.query('WFMPRE:YZERO?')[9:-1])
    yoff = float(tek.query('WFMPRE:YOFF?')[9:-1])
    xincr = float(tek.query('WFMPRE:XINCR?')[9:-1])

    # Acquire data and convert binary to data
    tek.write('CURVE?')
    data = tek.read_raw()
    headerlen = 2 + int(data[1])
    header = data[:headerlen]
    ADCwave = data[headerlen:-1]
    ADCwave = np.array(unpack('%sB' % len(ADCwave), ADCwave))

    # Convert data to scale
    V1 = (ADCwave - yoff) * ymult + yzero
    t1 = np.arange(0, xincr * len(V1), xincr)

    #%% Channel 1
    # Prepare scope for acquisition
    tek.write('DATA:SOU CH2')
    tek.write('DATA:WIDTH 1')
    tek.write('DATA:ENC RPB')

    # Get horz/vert settings from scope
    ymult = float(tek.query('WFMPRE:YMULT?')[9:-1])
    yzero = float(tek.query('WFMPRE:YZERO?')[9:-1])
    yoff = float(tek.query('WFMPRE:YOFF?')[9:-1])
    xincr = float(tek.query('WFMPRE:XINCR?')[9:-1])

    # Acquire data and convert binary to data
    tek.write('CURVE?')
    data = tek.read_raw()
    headerlen = 2 + int(data[1])
    header = data[:headerlen]
    ADCwave = data[headerlen:-1]
    ADCwave = np.array(unpack('%sB' % len(ADCwave), ADCwave))

    # Convert data to scale
    V2 = (ADCwave - yoff) * ymult + yzero
    t2 = np.arange(0, xincr * len(V2), xincr)

    # Save data
    if not os.path.exists('ScopeData'):
        os.makedirs('ScopeData')

    with open('ScopeData/' + filename, 'w') as f:
        f.write('t1 (s), V1 (V), t2 (s), V2 (V)\n')
        for i in range(0, len(V2)):
            f.write(str(t1[i]) + ',' + str(V1[i]) + ',' +  str(t2[i]) + ',' + str(V2[i]) + '\n')

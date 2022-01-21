# -*- coding: utf-8 -*-
"""
Functions to capture oscilloscope data. The curves are saved into a single
file within the 'ScopeData' directory.

Version 1.1 (2022-01-21)
Daan Wielens - Researcher at ICE/QTM
University of Twente
"""

import visa
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt
import time
from datetime import datetime
import os

def getScope(filename, samplename, GPIBaddr=1):
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

    # Check if samplename is correctly formatted
    if not samplename:
        raise ValueError('No sample identifier was provided. Please provide a sample identifier in the header of your measurement script.')
    else:
        sampledate = samplename.split('_')[0]
        try:
            dt_obj = datetime.strptime(sampledate, '%Y-%m-%d')
            # If the sample date is OK, check/create the folder for data storage
            if not os.path.isdir('Data/' + samplename):
                os.mkdir('Data/' + samplename)
        except Exception:
            raise ValueError('The sample identifier should have the following format: YYYY-MM-DD_<Sample-name>.')

    # Save data
    if not os.path.exists('Data/' + samplename + '/ScopeData'):
        os.makedirs('Data/' + samplename + '/ScopeData')

    with open('Data/' + samplename + '/ScopeData/' + filename, 'w') as f:
        f.write('t1 (s), V1 (V), t2 (s), V2 (V)\n')
        for i in range(0, len(V2)):
            f.write(str(t1[i]) + ',' + str(V1[i]) + ',' +  str(t2[i]) + ',' + str(V2[i]) + '\n')

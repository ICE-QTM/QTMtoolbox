# -*- coding: utf-8 -*-
"""
Main script of the Python QTM measurement toolbox.

Version 2.1 (2021-12-09)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""
#%% Setup
import numpy as np

# Import device definitions
from instruments.curtime import *

# Connect to devices
ct = curtime()

# Define wait time between 'reaching setpoint' and 'taking measurement' (in seconds)
dtw = 3

# Define sample name
samplename = '2021-12-09_Test-sample'

# Define what variables need to be measured
meas_list = 'ct.time, ct.timems'

# Import measurement tools
from functions import qtmlab
meas_dict = qtmlab.generate_meas_dict(globals(), meas_list)
qtmlab.meas_dict = meas_dict
qtmlab.dtw = dtw
qtmlab.samplename = samplename
#%% Batch commands
"""
Add your batch commands below this comment. Alternatively, run commands individually
from the IPython console
"""

qtmlab.record(1, 10, 'test.csv')

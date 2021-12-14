# -*- coding: utf-8 -*-
"""
Main script of the Python QTM measurement toolbox.

Version 2.2 (2021-12-14)
Daan Wielens - Researcher at ICE/QTM
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
samplename = '2021-12-14_Test-sample'

# Define what variables need to be measured
meas_list = 'ct.time, ct.timems'

# Import measurement tools
from functions import qtmlab
from functions import qtmstartup
meas_dict = qtmlab.generate_meas_dict(globals(), meas_list)
qtmlab.meas_dict = meas_dict
qtmlab.dtw = dtw
qtmlab.samplename = samplename
#%% Batch commands
qtmstartup.copy_script(__file__, samplename)
"""
Add your batch commands below this comment. Alternatively, run commands individually
from the IPython console
"""

qtmlab.record(1, 10, 'test.csv')

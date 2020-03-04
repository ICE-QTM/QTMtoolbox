# -*- coding: utf-8 -*-
"""
Main script of the Python QTM measurement toolbox.

Version 2.0 (2020-03-04)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""
#%% Setup
import numpy as np

# Import device definitions
from instruments.Keith2400 import *

# Connect to devices
kb = Keithley2400(20)
kt = Keithley2400(22)

# Define wait time between 'reaching setpoint' and 'taking measurement' (in seconds)
dtw = 3

# Define what variables need to be measured
meas_list = 'kb.dcv, kt.dcv, kb.i, kt.i'

# Import measurement tools
from functions import qtmlab
meas_dict = qtmlab.generate_meas_dict(globals(), meas_list)
qtmlab.meas_dict = meas_dict
qtmlab.dtw = dtw
#%% Batch commands
"""
Add your batch commands below this comment. Alternatively, run commands individually
from the IPython console
"""

# -*- coding: utf-8 -*-
"""
Main script of the Python QTM measurement toolbox.

Version 1.0 (2018-08-24)
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

# Define what variables need to be measured (Chuan's measure string, containing "sr1.x,sr1.y,....")
meas_dict = {
        'kbg.dcv' : {
                'dev' : kb,
                'var' : 'dcv'
                },
        'kbg.i' : {
                'dev' : kb,
                'var' : 'i'
                },
        'ktg.dcv' : {
                'dev' : kt,
                'var' : 'dcv'
                },
        'ktg.i' : {
                'dev' : kt,
                'var' : 'i'
                }
        }

# Import measurement tools
from functions import qtmlab
qtmlab.meas_dict = meas_dict

#%% Batch commands
"""
Add your batch commands below this comment. Alternatively, run commands individually 
from the IPython console
"""

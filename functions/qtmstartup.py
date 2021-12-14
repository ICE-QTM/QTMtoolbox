# -*- coding: utf-8 -*-
"""
Created on Tue Dec 14 09:09:13 2021

@author: WielensDH
"""

import numpy as np
import shutil
import os
from datetime import datetime

def copy_script(filename, samplename):
    # Check if samplename is in the correct format
    sampledate = samplename.split('_')[0]
    try:
        dt_obj = datetime.strptime(sampledate, '%Y-%m-%d')
        # If the sample date is OK, check/create the folder for data storage
        if not os.path.isdir('Data/' + samplename):
            os.mkdir('Data/' + samplename)
    except Exception:
        raise ValueError('The sample identifier should have the following format: YYYY-MM-DD_<Sample-name>.')
        
    # Create scripts folder if non-existent
    if not os.path.isdir('Data/' + samplename + '/Scripts'):
        os.mkdir('Data/' + samplename + '/Scripts')
        
    # Copy script to folder, change filename to reflect current time
    fpath = os.path.dirname(filename)
    fbase = os.path.basename(filename)
    
    # Some people already put the date into the filename, so don't put it twice
    try:
        datestr = fbase[:10]
        dt_obj = datetime.strptime(datestr, '%Y-%m-%d')
        # If the line above runs without complications, use that date
        time_string = datetime.now().strftime('%H%M%S')
        fbase_new = datestr + '-' + time_string + fbase[10:]
    except Exception:
        # If the dt_obj assignment fails, run the following to append a full date string
        time_string = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        fbase_new = time_string + fbase
        
    shutil.copy2(filename, 'Data/' + samplename + '/Scripts/' + fbase_new)
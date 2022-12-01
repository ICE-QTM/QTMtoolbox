# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 13:37:38 2020
@author: Daan Wielens

Function to load data generated by the QTMtoolbox

---------------------------------------------------------------------------
Data structure:
    
    list QTMdata:
        |
        |--> class "variable"
                |
                |--> index (must be unique!)
                |
                |--> header name (not unique, e.g. for <sweep> when 
                |                 you both sweep and read a variable)
                |
                |--> data array 
                |--> variable type (s = SETpoint or g = GET value (== measured value))
---------------------------------------------------------------------------
"""

import numpy as np

# Every variable will be an object, added to a list.        
class variable:
    type = 'variable'
    def __init__(self, index, name, data, vartype):
        self.index = index
        self.name = name
        self.data = data
        self.vartype = vartype

# Parse the data
def parse_data(fname):
    try:
        QTMdata = []
        with open(fname) as file:
            
            # Extract header names
            head = [next(file) for x in range(3)]
            setget_vals = head[0].split('|')[1]
            head_names = head[2]   # Header line with variable names
            head_names = head_names.replace('.', '').replace('\n', '').split(', ')
    except Exception:
        return "no_meas_file"
    try:        
        # Extract data
        data = np.loadtxt(fname, delimiter=',', skiprows=3)
        
        # Create variables, add to QTMdata
        for i in range(len(head_names)):
            curvar = variable(i, head_names[i], data[:,i], setget_vals[i])
            QTMdata.append(curvar)
        return QTMdata
    except Exception:
        # If no data is present yet
        for i in range(len(head_names)):
            curvar = variable(i, head_names[i], '', '')
            QTMdata.append(curvar)
        return QTMdata

if __name__ == '__main__':
    fname = 'data.csv'
    x = parse_data(fname)

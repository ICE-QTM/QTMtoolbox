# -*- coding: utf-8 -*-
"""
Module to request the current time in different formats.
The module can not be named 'time' as this would interfere with the
built-in 'time' module of Python.

Note: timestamps are given since the epoch (01-01-1970 00:00:00).

Version 1.1.1 (2026-08-10)
Daan Wielens - Researcher at ICE/QTM
University of Twente
"""

import time

class curtime:
    """
    """
    type = 'Current time'
    def __init__(self):
        self.time = time

    def read_time(self):
        """
        Returns the epoch clocktime (given in seconds from 1970-01-01 00:00)
        as a value in seconds. 
        
        Returns
        -------
        float
            epoch time in seconds
        """
        # Returns time in seconds as float number
        return time.time()

    def read_timens(self):
        """
        Returns the epoch clocktime (given in seconds from 1970-01-01 00:00)
        as a value in nanoseconds. 
        
        Returns
        -------
        int
            epoch time in nanoseconds
        """
        # Returns time in nanoseconds as integer value
        return int(time.time_ns())

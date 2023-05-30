# -*- coding: utf-8 -*-
"""
Module to request the current time in different formats.
The module can not be named 'time' as this would interfere with the
built-in 'time' module of Python.

Note: timestamps are given since the epoch (01-01-1970 00:00:00).

Version 1.1 (2023-05-30)
Daan Wielens - Researcher at ICE/QTM
University of Twente
d.h.wielens@utwente.nl
"""

import time

class curtime:
    type = 'Current time'
    def __init__(self):
        self.time = time

    def read_time(self):
        # Returns time in seconds as float number
        return time.time()

    def read_timens(self):
        # Returns time in nanoseconds as integer value
        return time.time_ns()

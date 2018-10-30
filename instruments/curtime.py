# -*- coding: utf-8 -*-
"""
Module to request the current time in different formats.
The module can not be named 'time' as this would interfere with the
built-in 'time' module of Python

Version 1.0 (2018-10-16)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""

import time

class curtime:
    type = 'Current time'
    def __init__(self):
        self.time = time

    def read_time(self):
        resp = round(time.time())
        return resp

    def read_timems(self):
        resp = round(time.time()*1000)
        return resp

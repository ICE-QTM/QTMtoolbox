# -*- coding: utf-8 -*-
"""
Module to interact with the ICEoxford Nexus software.
Uses TCP/IP sockets to communicate with the device.

Based on example code provided by ICEoxford.

Version 0.1 (2026-08-21)
Daan Wielens - Researcher at ICE/QTM
University of Twente
"""

import socket
import base64
import struct

class ICEoxfordNexus:
    type = 'ICEoxford Nexus'

    def __init__(self, IPaddress, port=6340):
        # Port should be a number, not a string
        if not isinstance(port, int):
            port = int(port)
        # Prepare socket instance
        self.s = socket.socket()
        self.s.connect((IPaddress, port))
        
    def query(self, val):
        self.s.sendall((str(val) + '\r\n').encode('ascii'))
        resp = self.s.recv(262144).decode('ascii', errors='replace')
        return resp.strip()
    
    def start_streaming(self):
        print(self.query('Set_Remote'))
        print(self.query('Start_Streaming(Interval=1000,Port=6341,Channels=All,Status=All)'))
        
    def stop_streaming(self):
        print(self.query('Stop_Streaming'))
    
    def close(self):
        print(self.query('Set_Local'))
        self.s.close()
    
    def get_text_inside_brackets(text):
        """
        Return the text inside brackets, e.g. Name(A,B,C) -> A,B,C.
        Function by ICEoxford.
        """
        start = text.find("(")
        end = text.rfind(")")
     
        if start == -1 or end == -1:
            return text
     
        return text[start + 1:end] 
    
    def format_value(value):
        """
        Format values so they are easier to read.
        Function by ICEoxford.
        """
        if value is None:
            return "N/A"
     
        if value == 0:
            return "0.000000"
     
        if abs(value) >= 100000:
            return f"{value:.0f}"
     
        if abs(value) >= 1000:
            return f"{value:.2f}"
     
        if abs(value) >= 1:
            return f"{value:.6f}"
     
        return f"{value:.6e}"
        
        def get_channel_names(self):
            resp = self.get_text_inside_brackets(self.query('Get_Stream_Names'))
            return [name.strip() for name in resp.split(",") if name.strip()]
        
    def get_values(self):
        """
        Ask Nexus for live data and decode each value.
        Function by ICEoxford; is modified to match class implementation.
        """
        resp = self.query('Send_Data')
        data_text = self.get_text_inside_brackets(resp)
     
        values = []
     
        for item in data_text.split(","):
            item = item.strip()
     
            if item == "":
                values.append(None)
                continue
     
            try:
                raw_bytes = base64.b64decode(item)
                value = struct.unpack(">d", raw_bytes)[0]
                values.append(value)
            except Exception:
                values.append(None)
     
        return values
        
        
        
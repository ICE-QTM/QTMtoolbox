"""Module containing a class to interface with a Quantum Dynamics PPMS DynaCool

Module to interact with a Quantum Design PPMS Dynacool system.
Uses Python for .NET to communicate (install via " pip install pythonnet")

Version 1.1 (2021-04-12)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com

Based on https://github.com/hinnefe2/ppms and https://github.com/masonlab/labdrivers

Installation requirements:
- Make sure to install .NET framework 3.5 on the MultiVu computer (for local use)
- Acquire the QDInstrument.dll file from the Quantum Design Pharos platform and put it in the root of QTMtoolbox
- Make sure that the QTMtoolbox folder is not read-only (through Properties window of Windows Explorer)
- Run both Python and MultiVu as administrator
"""

import clr

# load the C# .dll supplied by Quantum Design
try:
    clr.AddReference('QDInstrument')
except:
    if clr.FindAssembly('QDInstrument') is None:
        print('Could not find QDInstrument.dll')
    else:
        print('Found QDInstrument.dll at {}'.format(clr.FindAssembly('QDInstrument')))
        print('Try right-clicking the .dll, selecting "Properties", and then clicking "Unblock"')

# import the C# classes for interfacing with the PPMS
from QuantumDesign.QDInstrument import *

QDI_DYNACOOL_TYPE = QDInstrumentBase.QDInstrumentType.DynaCool
DEFAULT_PORT = 11000

class Dynacool:
    """Thin wrapper around the QuantumDesign.QDInstrument.QDInstrumentBase class"""

    def __init__(self, ip_address):
       self.qdi_instrument = QDInstrumentFactory.GetQDInstrument(QDI_DYNACOOL_TYPE, False, ip_address, DEFAULT_PORT)

    def read_temp(self):
        # Temperature in Kelvin
        resp = self.qdi_instrument.GetTemperature(0, 0)[1]
        return resp
    
    def write_temp(self, temp, rate):
        # Temperature in Kelvin and rate in Kelvin/min
        return self.qdi_instrument.SetTemperature(temp, rate, 0)

    def read_fvalue(self):
        # Field in Gauss ( = Oersted)
        resp = self.qdi_instrument.GetField(0, 0)[1]
        return resp
    
    def write_fvalue(self, field, rate):
        # Field in Gauss and rate in Gauss/sec
        return self.qdi_instrument.SetField(field, rate, 0, 0)

    def waitForTemperature(self, delay=5, timeout=600):
        #Pause execution until the PPMS reaches the temperature setpoint.
        return self.qdi_instrument.WaitFor(True, False, False, False, delay, timeout)

    def waitForField(self, delay=5, timeout=600):
        #Pause execution until the PPMS reaches the field setpoint.
        return self.qdi_instrument.WaitFor(False, True, False, False, delay, timeout)

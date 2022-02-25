"""Module containing a class to interface with a Quantum Dynamics PPMS DynaCool

Module to interact with a Quantum Design PPMS Dynacool system.
Uses Python for .NET to communicate (install via " pip install pythonnet")

Version 1.1 (2021-09-01)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com

Based on https://github.com/hinnefe2/ppms and https://github.com/masonlab/labdrivers
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

    def __init__(self, ip_address='127.0.0.1'):
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
    
    def waitForPosition(self, delay=5, timeout=600):
        #Pause execution until the PPMS reaches the position setpoint.
        return self.qdi_instrument.WaitFor(False, False, True, False, delay, timeout)
        
    def write_PPMScommand(self, command):
        return self.qdi_instrument.SendPPMSCommand(command, '','', 0, 0)
    
    def read_position(self):
        resp = self.qdi_instrument.GetPosition("Horizontal Rotator", 0, 0)[1]
        return resp
    
    def write_position(self, position, speed=10, mode=0):
        # Mode: 0 = GoToPosition, 1 = MoveToLimitAndDefinePosition, 2 = DefinePosition
        self.qdi_instrument.SetPosition("Horizontal Rotator", position, speed, mode)
        
    def read_position_status(self):
        resp = self.qdi_instrument.GetPosition("Horizontal Rotator", 0, 0)[2]    
        options = ['Position unknown', 'At target', 'Unused2', 'Unused3', 'Unused4', 'Moving', 'Unused6',
                   'Unused7', 'At limit switch', 'At index switch', 'Unused10', 'Unused11', 'Unused12',
                   'Unused13', 'Unused14', 'Position failure']
        return options[resp]
        
    def read_chamber_status(self):
        resp = self.qdi_instrument.GetChamber(0)[1]
        options = ['Chamber unknown', 'Purged and sealed', 'Vented and sealed', 'Sealed', 'Purging', 'Venting',
                   'PreHiVac', 'HighVac', 'PumpContinuous', 'VentContinuous', 'Unused10', 'Unused11', 'Unused12',
                   'Unused13', 'Unused14', 'Chamber failure']
        return options[resp]
    
    def read_temp_status(self):
        resp = self.qdi_instrument.GetTemperature(0, 0)[2]
        options = ['Temperature unknown', 'Stable', 'Tracking', 'Unused3', 'Unused4', 'Near', 'Chasing', 'Filling',
                   'Unused8', 'Unused9', 'Standby', 'Unused11', 'Unused12', 'Disabled', 'Impedance not functioning', 'Temperature failure']
        return options[resp]
    
    def read_fvalue_status(self):
        resp = self.qdi_instrument.GetField(0, 0)[2]
        options = ['Magnet unknown', 'Stable and persistent', 'Warming switch', 'Cooling switch', 'Stable and driven', 'Iterating', 'Charging'
                   'Discharging', 'Current error', 'Unused9', 'Unused10', 'Unused11', 'Unused12', 'Unused13', 'Unused14', 'Magnet failure']
        return options[resp]
    
    def read_chamber_temp(self):
        resp = self.qdi_instrument.ReadSDO_F32(3, 6001, 4)
        return resp
        
    def status(self):
        print('DynaCool system status:')
        print('--------------------------------------')
        print('Temperature  : ' + str(self.read_temp()) + ' K.')
        print('     Status  : ' + self.read_temp_status())
        print('      Field  : ' + str(self.read_fvalue()) + ' Oe.')
        print('     Status  : ' + self.read_fvalue_status())
        try:
            print('   Position  : ' + str(self.read_position()) + ' deg.')
            print('     Status  : ' + self.read_position_status())
        except Exception:
            print( '    (!)        The rotator is not activated/installed!')
        print('    Chamber  : ' + self.read_chamber_status())
        print('--------------------------------------')

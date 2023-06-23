# -*- coding: utf-8 -*-
"""

ICE Triton 1 temperature controller

Version 1.1
Daan Wielens - ICE/QTM
University of Twente
daan@daanwielens.com

-------------------------------------------------------------------------------
This module interfaces with a Triton object to set temperatures and to 
automate procedures such as checking whether the system is at a certain
state.

"""

import time
import numpy as np

class NoTritonSystem(Exception):
    """
    The selected device is not a Triton system.
    """
    pass

class ICETriton1:
    type = 'ICE Triton 1'
    
    def __init__(self, TritonObj):
        self.oxT = TritonObj
        if self.oxT.type != 'Oxford Triton':
            raise NoTritonSystem('Expected a Triton RI.')
                            
    def EnterHighTemperature(self, final_setpoint = 3):
        stat =  self.oxT.read_action()
        if not 'Condensing' in stat:
            raise ValueError('The Triton should be in the condensing state, but I get:' + stat + '. Therefore, aborting the script.')
            
        # Check other system parameters before starting
        if (self.oxT.read_valve9() == 'OPEN') and (self.oxT.read_valve4() == 'CLOSE') and (self.oxT.read_turbspeed() > 999) and (self.oxT.read_temp8() < 1.3):
            print(' <> The system is currently in the low temperature regime.')
        else:
            raise ValueError('The system is not in the low temperature regime. Aborting script.')
            
        # Make sure system is not in closed-loop operation
        print(' <> Making sure that closed-loop operation is terminated.')
        self.oxT.loop_off()
        time.sleep(5)

        # Turn on Cernox
        print(' <> Turning on Cernox sensor')
        self.oxT.write_Tenab5('ON')    
        time.sleep(5)

        # Turn off turbo, close V9, open V4
        print(' <> Turn off the turbo pump, close V9, open V4')
        self.oxT.write_turbstate('OFF')
        time.sleep(5)
        if self.oxT.read_turbstate() != 'OFF':
            raise ValueError('   The turbo is not turning off. Aborting script.')
        time.sleep(1)
        self.oxT.write_valve9('CLOSE')
        time.sleep(1)
        self.oxT.write_valve4('OPEN')
        time.sleep(1)
        if (self.oxT.read_valve9() != 'CLOSE') or (self.oxT.read_valve4() != 'OPEN'):
            raise ValueError('   The valves are not responding. Aborting script.')
            
        # Turn on heaters - gently, since turbo is still ramping down!
        print(' <> Heating chamber and still with 20 mW until turbo is below 500 Hz')
        self.oxT.write_Hchamber(20000)
        time.sleep(5)
        self.oxT.write_Hstill(20000)
        time.sleep(5)
        turbSlow = False
        print('    Waiting for the turbo to slow down...')
        while not turbSlow:
            if self.oxT.read_turbspeed() < 500:
                turbSlow = True
                print(end='\r')
                print('      Turbo speed: < 500 Hz')
            else:
                time.sleep(10)
                print(end='\r')
                print('      Turbo speed: ' + str(self.oxT.read_turbspeed()) + ' Hz', end='\r')
                
        # Set heaters to 100 mW, wait until Cernox gives reasonable values, then switch to heater control
        print(' <> Apply 100 mW to mixing chamber and still, wait until Cernox readings are valid')
        self.oxT.write_Hchamber(100000)
        self.oxT.write_Hstill(100000)
        time.sleep(1)       
        
        # When the Cernox is underrange, its value is 1.415 K
        CernoxValid = False
        print('    Waiting for the Cernox to be above 1.5 K...')
        while not CernoxValid:
            if self.oxT.read_temp5() > 1.5:
                CernoxValid = True
                print(end='\r')
                print('      MC Cernox: > 1.5 K')
            else:
                print(end='\r')
                print('      MC Cernox: ' + str(self.oxT.read_temp5()) + ' K', end='\r')
                time.sleep(10)
                
        # With the Cernox at a valid reading, we can switch to closed loop control at the Cernox
        print('    Cernox is > 1.5 K, preparing closed loop control...')
        self.oxT.write_Tchan(5)
        time.sleep(2)
        self.oxT.write_Tset(final_setpoint)
        time.sleep(2)
        self.oxT.write_PID(5, 20, 20)
        time.sleep(2)
        self.oxT.write_range(30)
        time.sleep(2)
        # Turn off manual heaters
        self.oxT.write_Hstill(0)
        self.oxT.write_Hchamber(0)  
        time.sleep(2)
        print(' <> Turning on closed-loop control on the Cernox sensor')
        self.oxT.loop_on()
        time.sleep(10)
        self.oxT.write_Tset(final_setpoint)
        time.sleep(2) 
        self.oxT.write_range(30)
        time.sleep(2)
        if (self.oxT.read_Tset() == final_setpoint) and (self.oxT.read_range() > 0):
            print(' <> The Triton is now operating in high-temperature control mode. Please be aware that it may take an hour for all pressures to settle and thus for the temperature control to be accurate.')
        
    def CondenseSystem(self, wait_on_finishing = True):
        if self.oxT.read_temp8() > 10:
            raise ValueError('The mixing chamber should be below 10 K before one can condense. Please first precool the fridge. Aborting script.')
        print(' <> Turning off any heaters')
        # Prepare system: turn off closed loop, turn off heaters
        self.oxT.loop_off()
        time.sleep(5)
        self.oxT.write_Hchamber(0)
        self.oxT.write_Hstill(0)
        
        # Set Triton to condense
        print(' <> Starting the "Start the condensing" automation task.')
        self.oxT.query('SET:SYS:DR:ACTN:COND')
        time.sleep(10)
        
        if wait_on_finishing:
            print(' <> Waiting for the Triton to finish condensing:')
            print('      The system is considered to be fully condensed when')
            print('      the turbo is at full speed, meaning that the tank')
            print('      has been fully emptied. Note that the mixing chamber')
            print('      temperature can be still at an elevated value!')
            print(' ---------------------------------------------------------')
            finished = False
            Cernox = True
            while not finished:
                # Read sensors
                p1pres = self.oxT.read_pres1()
                p2pres = self.oxT.read_pres2()
                turbsp = self.oxT.read_turbspeed()
                temp8 = self.oxT.read_temp8()
                
                # Print values
                print(end='\r')
                print(' P1: ' + str(p1pres) + ' bar, P2: ' + str(p2pres) + ' bar, MC RuOx: ' + str(temp8) + ' K, Turbo speed: ' + str(turbsp) + ' Hz', end='\r')
                
                # Actions
                if Cernox:
                    if self.oxT.read_temp5() < 1.5:
                        self.oxT.write_Tenab5('OFF')
                        self.oxT.write_Tenab3('OFF')
                        Cernox = False
                
                if turbsp > 999:
                    finished = True
                
                time.sleep(5)
            
            print(' <> The Triton finished condensing.')
                
            
        
                
            

                
            
        
            
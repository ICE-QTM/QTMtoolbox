# -*- coding: utf-8 -*-
"""

ICE Triton 1 temperature controller

Version 2.1
Daan Wielens - ICE/QTM
University of Twente
-------------------------------------------------------------------------------

THIS SCRIPT IS SYSTEM SPECIFIC!! PLEASE DO NOT COPY IT FROM TRITON 1 TO 
TRITON 2 AS THERE ARE DIFFERENT LIMITS, PID VALUES AND CHECKS IN PLACE!!!

-------------------------------------------------------------------------------
This module interfaces with a Triton object to set temperatures and to 
automate procedures such as checking whether the system is at a certain
state.

Functions provided:
    
    get_heater_range_from_Tsetp()                   Returns the heater range required for the given setpoint
    write_setpoint_with_checks_start_PID_loop()     Performs the writing and checking of Tsetp, hsetp and can turn on PID loop
    change_setpoint()                               Writes the setpoint and heater range to Triton, changes PID values if loop was off
    get_regime()                                    Returns whether Triton is in low / high regime
    change_mixture_flow()                           Turns off the turbo pump, closes V9 and opens V4
    
    write_temp()                                    Automatically enters correct regime, then heats to provided value and waits for stabilization
    
    CondenseSystem()                                Brings system back to base temperature
    EnterMedTemperature()                           Brings system to medium temperature regime
    EnterHighTemperature()                          Brings system to high temperature regime 
    
    PrepareSampleExchange()                         Gradually collects the mixture (a bit slower compared to Oxford's method) which helps for 
                                                    a system in which the forepump is replaced by a stronger version which makes P5 exceed 1.1 bar
    
Normally, the end user should only use () which takes the temperature setpoint as argument. Choosing 0 K as setpoint will bring the system back to base.
To stop heating (but not actively recondensing), use trit.loop_off().      
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
            
    def get_heater_range_from_Tsetp(self, Tsetp):
        '''
        This helper function determines which heater range should be used for the 
        temperature setpoint. Note that these values are system-specific!

        Parameters
        ----------
        Tsetp : float
            Temperature setpoint (K).

        Returns
        -------
        float
            Heater output range (mA).

        '''
        T_vals = np.array([0, 0.01, 0.1, 0.3, 1.05])
        h_vals = np.array([0, 1, 3.16, 10, 31.6])
        return float(h_vals[np.where(T_vals <= Tsetp)[0][-1]])
    
    def write_setpoints_with_checks_start_PID_loop(self, Tsetp, hsetp, start_loop = True):
        # Round setpoint to mK
        Tsetp = np.round(Tsetp, 3)
        print(' <> Writing temperature setpoint and heater range')
        # Write Tsetp and check whether the Triton has correctly processed it
        correct_setpoint = False
        self.oxT.write_Tset(Tsetp)
        time.sleep(2)
        while not correct_setpoint:
            if self.oxT.read_Tset() != Tsetp:
                self.oxT.write_Tset(Tsetp)
                time.sleep(2)
            else:
                correct_setpoint = True
                time.sleep(2)
                print('    Temperature setpoint correct')
        # Write heater range and check if non-zero
        correct_setpoint = False
        self.oxT.write_range(hsetp)
        time.sleep(2)
        while not correct_setpoint:
            if self.oxT.read_range() == 0:
                self.oxT.write_range(hsetp)
                time.sleep(2)
            else:
                correct_setpoint = True
                time.sleep(2)
                print('    Heater range correct')
        if start_loop:
            print('    Turning on PID loop...')
            self.oxT.loop_on()
            time.sleep(10)
            # Triton can be bitchy, so write setpoint again to ensure that it has not changed the value while starting the control loop
            correct_setpoint = False
            self.oxT.write_Tset(Tsetp)
            time.sleep(2)
            while not correct_setpoint:
                if self.oxT.read_Tset() != Tsetp:
                    self.oxT.write_Tset(Tsetp)
                    time.sleep(2)
                else:
                    correct_setpoint = True
                    time.sleep(2)
        print('    Temperature control enabled: ' + str(int(Tsetp*1000)) + ' mK with range ' + str(hsetp) + ' mA.')
                
    def change_setpoint(self, Tsetp):
        hsetp = self.get_heater_range_from_Tsetp(Tsetp)
        # Check if the Triton's loop is already on, otherwise firstly write PID before turning it on and turn off irrelevant sensors
        if self.oxT.read_loop() == 'OFF':
            print(' <> Triton PID loop is off. Writing PID values and turning off irrelevant temperature sensors...')
            current_regime = self.get_regime()
            if current_regime == 'low':
                self.oxT.write_PID(10, 100, 0)
            elif current_regime == 'med':
                self.oxT.write_PID(5, 30, 0)
            elif current_regime == 'high':
                self.oxT.write_PID(5, 20, 20)
            time.sleep(2)            
            self.oxT.write_Tenab1('OFF')
            self.oxT.write_Tenab2('OFF')
            self.oxT.write_Tenab3('OFF')
            self.oxT.write_Tenab4('OFF')
            if current_regime != 'high':
                self.oxT.write_Tenab5('OFF')
            self.oxT.write_Tenab6('OFF')
            self.oxT.write_Tenab7('OFF')
            self.write_setpoints_with_checks_start_PID_loop(Tsetp, hsetp)
        else:
            self.write_setpoints_with_checks_start_PID_loop(Tsetp, hsetp, start_loop = False)                        
                            
    def get_regime(self):
        """
        Function to determine in which routine the Triton currently is. Returns
        an error if no regime can be determined, to make sure that the system
        does not start a heater job while in an unknown state.

        Returns
        -------
        string
            Regime of Triton. Either "low", "med" or "high".

        """
        # Request Triton parameters
        try:
            V4_stat = self.oxT.read_valve4()
            V9_stat = self.oxT.read_valve9()
            turb_speed = self.oxT.read_turbspeed()
            turb_stat = self.oxT.read_turbstate()
            T8_val = self.oxT.read_temp8()
            T5_val = self.oxT.read_temp5()
            Tcontrol = self.oxT.read_Tchan()
        except Exception:
            raise ValueError('The Triton does not provide all required values to determine its state. Aborting script.')
            
        # Determine regime
        try:
            trit_regime = ''
            if V4_stat == 'CLOSE' and V9_stat == 'OPEN' and turb_speed > 800:
                trit_regime = 'low'
            elif (T8_val > 1 or T5_val > 1) and V4_stat == 'OPEN' and V9_stat == 'CLOSE' and turb_stat == 'OFF':
                if Tcontrol == 8:
                    trit_regime = 'med'
                elif Tcontrol == 5 and T5_val > 1.8:
                    trit_regime = 'high'
            if trit_regime == '':
                raise ValueError('The conditions of the Triton do not match any regime. Please check the system state manually.')
            return trit_regime
        except Exception:
            raise ValueError('Something went wrong in determining the Triton regime.')
     
    def change_mixture_flow(self):
        """
        This function turns off the turbo pump of the Triton, then closes V9 to stop pumping on the tank, and then opens V4 to 
        ensure that gas can flow from the DU towards the tank when heaters start evaporating the bulk of the mixture. Excessive
        checks are in place to ensure that every step is executed correctly by the Triton RI.

        Returns
        -------
        None.

        """
        print(' <!> Changing the turbo pump and V4 / V9 to alter the amount of mixture circulating through the DU.')
        # --- Turbo pump ---
        print('    Turning off turbo pump')
        try:
            self.oxT.write_turbstate('OFF')
            time.sleep(5)
            if self.oxT.read_turbstate() != 'OFF': 
                raise ValueError(' <!> The turbo is apparently not turning off. Aborting script. Please check the system!')
        except Exception:
            raise ValueError('<!> Unable to read/control the turbo pump, so aborting the script. Please check the system!')
        # --- Valve 9 ---
        print('    Closing V9')
        try:
            self.oxT.write_valve9('CLOSE')
            time.sleep(2)
            if self.oxT.read_valve9() != 'CLOSE': 
                raise ValueError(' <!> Valve 9 did not close. Aborting script. Please check the system!')
        except Exception:
            raise ValueError('<!> Unable to read/control valve 9, so aborting the script. Please check the system!')            
        # --- Valve 4 ---
        print('    Opening V4')
        try:
            self.oxT.write_valve4('OPEN')
            time.sleep(2)
            if self.oxT.read_valve4() != 'OPEN': 
                raise ValueError(' <!> Valve 4 did not open. Aborting script. Please check the system!')
        except Exception:
            raise ValueError('<!> Unable to read/control valve 4, so aborting the script. Please check the system!') 
        
    def write_temp(self, Tsetp):
        '''
        Changes the temperature setpoint of the Triton. Based on the current state and the final setpoint
        the system automatically decides whether it has to change 'regime'. A setpoint of 0 will bring 
        the system to base temperature.

        Parameters
        ----------
        Tsetp : float
            The temperature setpoint at which the Triton should stabilize.

        Returns
        -------
        None.

        '''
        # Do not allow automated control above 10 K
        if Tsetp > 10:
            raise ValueError('<!> We do not allow automated control above 10 K. Please perform the required commands manually. Measurements above 10 K can be dangerous when magnet operation is required.')
        
        # If setpoint is zero, simply condense
        if Tsetp == 0:
            self.CondenseSystem()

        current_regime = self.get_regime()
        # Determine what to do - setpoint in low temperature regime
        if Tsetp <= 1:
            # System needs to be or go to low temperature mode
            if current_regime == 'low':
                # Write setpoint to write_lowT
                self.oxT.write_Tchan(8)
                self.change_setpoint(Tsetp)
            else:
                self.CondenseSystem()
                # Wait for Triton to be below 1 K before preparing heater! Last time Triton was 1.3 K when exiting CondenseSystem so the state was unknown!
                print('    Waiting for the Triton temperature to be < 1 K...')
                system_low = False
                while not system_low:
                    T8 = self.oxT.read_temp8()                
                    if T8 < 1:
                        system_low = True
                        print(end='\r')
                        print('      RuOx temperature: ' + str(T8) + ' K.')
                    else:
                        print(end='\r')
                        print('      RuOx temperature: ' + str(T8) + ' K.', end='\r')
                        time.sleep(5)    
                    
                self.change_setpoint(Tsetp)

        # Determine what to do - setpoint in medium temperature regime
        elif Tsetp > 1 and Tsetp < 2:
            if current_regime == 'low':
                # System needs to warm up, shut down turbo and swap V4/V9 pos
                self.EnterMedTemperature(Tsetp)
            if current_regime == 'med':
                # Simply change heater
                self.change_setpoint(Tsetp)
            if current_regime == 'high':
                # To achieve sufficient cooling one has to condense, then warm up to the setpoint. Takes long time!
                print(' <!> The system will firstly condense and then heat towards the medium temperature.')
                self.CondenseSystem()
                self.EnterMedTemperature(Tsetp)

        # Determine what to do - setpoint in high temperature regime                
        elif Tsetp >= 2:
            if current_regime == 'low':
                # System needs to warm up fully, shut down turbo and swap V4/V9 pos, change Tchan and use both heaters
                self.EnterHighTemperature(Tsetp)
            if current_regime == 'med':
                # Simply change heater
                self.EnterHighTemperature(Tsetp)
            if current_regime == 'high':
                self.change_setpoint(Tsetp)

    def CondenseSystem(self, wait_on_finishing = True):
        if self.oxT.read_temp8() > 10:
            raise ValueError('The mixing chamber should be below 10 K before one can condense. Please use "Full Cooldown" from the Triton control software to condense. Aborting script.')
        print(' <> Turning off any heaters')
        # Prepare system: turn off closed loop, turn off heaters
        self.oxT.loop_off()
        time.sleep(5)
        self.oxT.write_Hchamber(0)
        self.oxT.write_Hstill(0)
        # Set temperature control channel to 8 as any future heating steps start from there
        self.oxT.write_Tchan(8)
        time.sleep(2)        
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
                
                if turbsp > 995:
                    finished = True
                
                time.sleep(5)
            
            print(' <> The Triton finished condensing. Mixing chamber temperature is currently ' + str(self.oxT.read_temp8() * 1000) +  ' mK.')

    def EnterMedTemperature(self, Tsetp = 1.2):
        # This script should only be called when the Triton is in the low temperature regime. It does not work when approached from a high temperature state.
        if self.get_regime() == 'high':
            raise ValueError('The Triton can not go into the medium temperature regime when it starts from the high temperature regime.')
        if self.get_regime() == 'low':
            print(' <> Entering the medium temperature regime while starting from the low temperature regime.')
            print('    Disabling any current PID control loop')
            self.oxT.loop_off()
            time.sleep(10)
            print('    Writing PID values for medium regime')
            self.oxT.write_PID(5, 30, 0)
            # Set temperature control channel to 8
            self.oxT.write_Tchan(8)            
            time.sleep(2)
            # Change valves and turbo
            self.change_mixture_flow()
            # While the turbo is spinning down, start heating at low power (range 10 mA)
            print('    Start heating with 5 mW heater range until the turbo is at low enough speed ( < 500 Hz)')
            self.oxT.write_Tchan(8)
            time.sleep(2)
            self.oxT.write_Hchamber(5000)
            time.sleep(2)
            # Waiting for turbo to slow down
            turb_slow = False
            while not turb_slow:
                turb_speed = self.oxT.read_turbspeed()                
                if turb_speed < 500:
                    turb_slow = True
                    print(end='\r')
                    print('      Turbo speed: ' + str(turb_speed) + ' Hz.')
                else:
                    print(end='\r')
                    print('      Turbo speed: ' + str(turb_speed) + ' Hz.', end='\r')
                    time.sleep(5)                
            
            # Start heating with required range
            self.oxT.write_Hchamber(0)
            time.sleep(2)
            self.change_setpoint(Tsetp) 
            print(' <> The system is now in the medium temperature regime.')
                    
    def EnterHighTemperature(self, Tsetp = 3):
        
        '''
        - If still in low temp regime, change valves and perform 'regular' routine
        - If already in med temp regime with valves changed, just start blasting 100 mW on both plates
        '''
        current_regime = self.get_regime() 
        if current_regime == 'low':
            print(' <> System is in low temperature mode. Preparing system to turn off turbo / change valves.')
            print('    Turning off PID control')
            self.oxT.loop_off()
            time.sleep(5)
            print('    Turning on Cernox sensor (Ch. 5)')
            self.oxT.write_Tenab5('ON')
            time.sleep(5)
            # Turn off turbo, close V9, open V4
            self.change_mixture_flow()
            # Turn on heaters - gently, since turbo is still ramping down!
            print('    Heating chamber and still with 20 mW until turbo is below 500 Hz')
            self.oxT.write_Hchamber(20000)
            time.sleep(1)
            self.oxT.write_Hstill(20000)
            time.sleep(1)
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
                    
        if current_regime == 'med':
            print(' <> Coming from the medium regime. Turning on Cernox sensor')
            self.oxT.write_Tenab5('ON')
            time.sleep(5)
            print('    Turning off PID loop')
            self.oxT.loop_off()
        
        print(' <> The system is now in the medium regime.')
        # Set heaters to 100 mW, wait until Cernox gives reasonable values, then switch to heater control
        print(' <> Apply 100 mW to mixing chamber and still, wait until Cernox readings are valid')
        self.oxT.write_Hchamber(100000)
        time.sleep(1)
        self.oxT.write_Hstill(100000)
        time.sleep(1)       
        
        # When the Cernox is underrange, its value is 1.415 K.
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
        self.oxT.write_PID(5, 20, 20)
        time.sleep(2)
        # Turn off manual heaters
        self.oxT.write_Hstill(0)
        self.oxT.write_Hchamber(0)  
        time.sleep(2)
        # Write temperature and heater setpoints
        self.write_setpoints_with_checks_start_PID_loop(Tsetp, 30)
        print(' <> The Triton is now operating in high-temperature control mode. Please be aware that it may take an hour for all pressures to settle and thus for the temperature control to be accurate.')                
            
    def PrepareSampleExchange(self):
        
        '''
        - Firstly construct this piece of code for 'low temperature regime', later add med/high.
        '''
        current_regime = self.get_regime() 
        if current_regime == 'low':
            print(' <!> ---- Preparing system for sample exchange ---- ')
            print(' <> System is in low temperature mode. Preparing system to turn off turbo / change valves.')
            print('    Turning off PID control')
            self.oxT.loop_off()
            time.sleep(5)
            print('    Turning on Cernox sensor (Ch. 5) and still plate sensor')
            self.oxT.write_Tenab5('ON')
            self.oxT.write_Tenab3('ON')
            time.sleep(5)
            # Turn off turbo, close V9, open V4
            self.change_mixture_flow()
            # Turn on heaters - gently, since turbo is still ramping down!
            print('    Heating chamber and still with 20 mW until turbo is below 500 Hz')
            self.oxT.write_Hchamber(20000)
            time.sleep(1)
            self.oxT.write_Hstill(20000)
            time.sleep(1)
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
                    
        else:
            raise ValueError('The PrepareSampleExchange routine only works when the system is currently in the low temperature regime. Please firstly condense, then run the routine again.')
        
        '''
        Issue: the Kashiyama Neodry 30G forepump is more powerful than the Adixen ACP28. When the still evaporates the bulk of the helium, this normally creates a pressure
        spike in the still tube (P3) and is then 'slowly' pumped by the Adixen. The Kashiyama is faster, so P3 spikes at a lower value, but as a result more gas is pushed
        to the back of the forepump (P5) which is only a small volume. Hence, the pressure there exceeds safe values and the Triton control stops automation. Here, we try 
        to mitigate this issue.
        '''
        print(' <> Applying heater power to the mixing chamber and still plate.')
        # Do some 'slow' safety checking here (aiding the Triton 'safety checks')
        safe_state = True
        self.oxT.write_Hchamber(100000)
        time.sleep(1)

        print('', end='\r')
        while safe_state:
            
            # Regulate still power based on P5 - only change value if heater currently has a different value (changing heater value is a slow process, minimize write cycles)
            P1 = self.oxT.read_pres1()
            P5 = self.oxT.read_pres5()
            T3 = self.oxT.read_temp3()
            Hs = self.oxT.read_Hstill()
            print('', end='\r')
            print('P1 = ' + str(P1).ljust(10) + ' bar, P5 = ' + str(P5).ljust(10) + ' bar, Tstill = ' + str(T3).ljust(10) + ' K, Hstill = ' + str(Hs).ljust(8) + ' uW', end='\r')
            
            if P5 < 0.2 and np.abs(Hs - 40000) > 20:               
                self.oxT.write_Hstill(40000)
                time.sleep(1)
            elif P5 < 0.3 and np.abs(Hs - 10000) > 20:
                self.oxT.write_Hstill(10000)
                time.sleep(1)
            elif P5 < 0.5 and np.abs(Hs) > 20:
                self.oxT.write_Hstill(0)
                time.sleep(1)
            else:
                time.sleep(1)            
            if P5 > 1:
                safe_state = False
                print('', end='\r\n')
                
            # Check if system is ready (tank pressure > 80%):
            P_finish = 0.8 * 0.68 # Tank pressure (2026-04)
            if P1 > P_finish:
                print('', end='\r\n')
                break      
            
        # Finished
        if safe_state:
            print(' <> The Triton is ready for sample exchange. Please start the "Start a sample change" wizard in the Triton System Control software.')
            self.oxT.write_Hchamber(20000)
            time.sleep(1)
            self.oxT.write_Hstill(20000)
            time.sleep(1)
        else:
            print(' <!> An error occurred during the preparation for sample exchange. Turning off heaters. The Triton System Control takes care of the valves. Please contact Daan for further instructions.')
            # Turn off manual heaters
            self.oxT.write_Hstill(0)
            time.sleep(1)
            self.oxT.write_Hchamber(0)  
            time.sleep(1)
            

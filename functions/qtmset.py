# -*- coding: utf-8 -*-
"""
Functions that can be used to change device settings within the QTMlab framework.

Available functions:
    setsens(device, vrange_in_mV)

Version 1.0 (2019-03-20)
Joris Voerman - PhD at ICE/QTM - j.a.voerman@utwente.nl
University of Twente
"""

def setsens(device, vrange_in_mV):
    """
    The write command sets a new lock-in sensitivity.
    It translates voltage ranges to lock-in sensitivity numbers.
    It achieves this by sorting the user value into the array of numbers. The lock-in
    should be send the index number of this array!
    """
    sens = np.array([2e-9, 5e-9, 1e-8, 2e-8, 5e-8, 1e-7, 2e-7, 5e-7, 1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2, 1e-1, 2e-1, 5e-1, 1])
    vrange = vrange_in_mV/1000  #User input is given in mV
    check = 19 #19 is 5 mV, which is a good starting point to start the sorting.
    Sorted = False
    while Sorted == False:
        #This statement checks if we have found the correct place to put our value
        if vrange <= sens[check] and vrange >= sens[check-1]:
            Sorted = True
            if vrange == sens[check-1]:
                write_command = getattr(device, 'write_sens')
                write_command(check-1)
            else:
                write_command = getattr(device, 'write_sens')
                write_command(check)
            return
        #If the value was too small we move to lower indices
        elif vrange < sens[check]:
            check = check-1
        #If the value was too high we move to higher indices
        else:
            check = check+1
        #If the algorithm goes off the rails: Catch it and provide feedback to the user
        if check == 0 or check == 28:
            Sorted = True
            print('Unable to determine the sensitivity. Correct syntax: qtmlab.setsens(device,range)')
            write_command = getattr(device, 'write_sens')
            write_command(check)

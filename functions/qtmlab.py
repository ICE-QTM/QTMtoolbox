# -*- coding: utf-8 -*-
"""
Functions that can be used in measurements within the QTMlab framework.

Available functions:
    move(device, variable, setpoint, rate)
    measure()
    sweep(device, variable, start, stop, rate, npoints, filename)

Version 1.6 (2019-05-20)
Daan Wielens   - PhD at ICE/QTM - daan@daanwielens.com
Joris Voerman  - PhD at ICE/QTM - j.a.voerman@utwente.nl
University of Twente
"""
import time
import numpy as np
import os
import math

meas_dict = {}

# Global settings
dt = 0.02           # Move timestep [s]
dtw = 1             # Wait time before measurement [s]

# Create Data directory
if not os.path.isdir('Data'):
    os.mkdir('Data')

def move(device, variable, setpoint, rate):
    """
    The move command moves <variable> of <device> to <setpoint> at <rate>.
    Example: move(KeithBG, dcv, 10, 0.1)

    Note: a variable can only be moved if its instrument class has both
    write_var and read_var modules.
    """

    # Oxford Magnet Controller - timing issue fix
    """
    For Oxford IPS120-10 Magnet Controllers, timing is a problem.
    Sending and receiving data over GPIB takes a considerable amount
    of time. We therefore change the magnet's rate and issue a single set
    command. Then, we check every once in a while (100 ms delay) if it is
    already at its setpoint.
    """
    #---------------------------------------------------------------------------
    devtype = str(type(device))[1:-1].split('.')[-1].strip("'")
    if devtype == 'ips120':
        read_command = getattr(device, 'read_' + variable)
        cur_val = float(read_command())

        ratepm = round(rate * 60, 3)
        if ratepm >= 0.4:
            ratepm = 0.4
        # Don't put rate to zero if move setpoint == current value
        if ratepm == 0:
            ratepm = 0.1

        write_rate = getattr(device, 'write_rate')
        write_rate(ratepm)

        write_command = getattr(device, 'write_' + variable)
        write_command(setpoint)

        reached = False
        cntr = 0
        while not reached:
            time.sleep(0.1)
            cur_val = float(read_command())
            if round(cur_val, 2) == round(setpoint, 2):
                reached = True
            else:
                cntr += 1
            # If the device is still not there, send the setpoint again
            if cntr == 5:
                time.sleep(0.1)
                write_command(setpoint)

        return
    #---------------------------------------------------------------------------

    # Get current Value
    read_command = getattr(device, 'read_' + variable)
    cur_val = float(read_command())

    # Determine number of steps
    Dt = abs(setpoint - cur_val) / rate
    nSteps = int(round(Dt / dt))
    # Only move when setpoint != curval, i.e. nSteps != 0
    if nSteps != 0:
        # Create list of setpoints and change setpoint by looping through array
        move_curve = np.round(np.linspace(cur_val, setpoint, nSteps), 3)
        for i in range(nSteps):
            write_command = getattr(device, 'write_' + variable)
            write_command(move_curve[i])
            time.sleep(dt)

def measure(md=None):
    """
    The measure command measures the values of every <device> and <variable>
    as specified in the 'measurement dictionary ', meas_dict.
    """
    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    # Loop over list of devices
    data = np.zeros(len(md))
    i = 0
    for device in md:
        # Retrieve and store data
        meas_command = getattr(md[device]['dev'], 'read_' + md[device]['var'])
        data[i] = float(meas_command())
        i += 1

    return data


def sweep(device, variable, start, stop, rate, npoints, filename, sweepdev=None, md=None, scale='lin'):
    """
    The sweep command sweeps the <variable> of <device>, from <start> to <stop>.
    Sweeping is done at <rate> and <npoints> are recorded to a datafile saved
    as <filename>.
    For measurements, the 'measurement dictionary', meas_dict, is used.
    """
    print('Starting a sweep of "' + variable + '" from ' + str(start) + ' to ' + str(stop) + ' in ' + str(npoints) + ' ('+ str(scale) + ' spacing)' +' steps with rate ' + str(rate) + '.')

    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    # Make sure that the datafile is stored in the 'Data' folder
    filename = 'Data/' + filename

    # Initialise datafile
    append_no = 0;
    while os.path.isfile(filename):
        append_no += 1 #Count the number of times the file already existed
        filename = filename.split('.')
        if append_no == 1: #The first time the program finds the unedited filename. We save it as the base
            filename_base = filename[0]
        filename = filename_base + '_' + str(append_no) +'.' + filename[1] #add "_N" to the filename where N is the number of loop iterations
        if os.path.isfile(filename) == False: #Only when the newly created filename doesn't exist: inform the user. The whileloop stops.
            print('The file already exists. Filename changed to: ' + filename)
    # Get specified variable name, or use default
    if sweepdev is None:
        sweepdev = 'sweepdev'
    header = sweepdev
    # Add device of 'meas_list'
    for dev in md:
        header = header + ', ' + dev
    # Write header to file
    with open(filename, 'w') as file:
        file.write(header + '\n')

    # Move to initial value
    print('Moving to the initial value...')
    move(device, variable, start, rate)

    # Create sweep_curve
    if scale == 'lin':
        sweep_curve = np.round(np.linspace(start, stop, npoints), 3)
    if scale == 'log':
        sweep_curve = np.round(np.logspace(np.log10(start), np.log10(stop), npoints), 3)

    # Perform sweep
    for i in range(npoints):
        # Move to measurement value
        print('Sweeping to: {}'.format(sweep_curve[i]))
        move(device, variable, sweep_curve[i], rate)
        # Wait, then measure
        print('   Waiting for measurement...')
        time.sleep(dtw)
        print('   Performing measurement.')
        data = np.hstack((sweep_curve[i], measure()))

        # Add data to file
        datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
        with open(filename, 'a') as file:
            file.write(datastr + '\n')


def waitfor(device, variable, setpoint, threshold=0.05, tmin=60):
    """
    The waitfor command waits until <variable> of <device> reached
    <setpoint> within +/- <threshold> for at least <tmin>.
    Note: <tmin> is in seconds.
    """
    print('Waiting for "'  + variable + '" to be within ' + str(setpoint) + ' +/- ' + str(threshold) + ' for at least ' + str(tmin) + ' seconds.')
    stable = False
    t_stable = 0
    while not stable:
        # Read value
        read_command = getattr(device, 'read_' + variable)
        cur_val = float(read_command())
        # Determine if value within threshold
        if abs(cur_val - setpoint) <= threshold:
            # Add time to counter
            t_stable += 10
        else:
            # Reset counter
            t_stable = 0
        time.sleep(10)
        # Check if t_stable > tmin
        if t_stable >= tmin:
            stable = True
            print('The device is stable.')

def record(dt, npoints, filename, md=None):
    """
    The record command records data with a time interval of <dt> seconds. It
    will record data for a number of <npoints> and store it in <filename>.
    """
    print('Recording data with a time interval of ' + str(dt) + ' seconds for (up to) ' + str(npoints) + ' points. Hit <Ctrl+C> to abort.')
    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    # Make sure that the datafile is stored in the 'Data' folder
    filename = 'Data/' + filename

    # Initialise datafile
    append_no = 0;
    while os.path.isfile(filename):
        append_no += 1 #Count the number of times the file already existed
        filename = filename.split('.')
        if append_no == 1: #The first time the program finds the unedited filename. We save it as the base
            filename_base = filename[0]
        filename = filename_base + '_' + str(append_no) +'.' + filename[1] #add "_N" to the filename where N is the number of loop iterations
        if os.path.isfile(filename) == False: #Only when the newly created filename doesn't exist: inform the user. The whileloop stops.
            print('The file already exists. Filename changed to: ' + filename)

    # Build header
    header = 'time'
    for dev in md:
        header = header + ', ' + dev
    # Write header to file
    with open(filename, 'w') as file:
        file.write(header + '\n')

    # Perform record
    for i in range(npoints):
        print('Performing measurement at t = ' + str(i*dt) + ' s.')
        data = measure()
        datastr = (str(i*dt) + ', ' + np.array2string(data, separator=', ')[1:-1]).replace('\n', '')
        with open(filename, 'a') as file:
            file.write(datastr + '\n')
        time.sleep(dt)

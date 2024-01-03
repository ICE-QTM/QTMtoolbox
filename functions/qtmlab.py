# -*- coding: utf-8 -*-
"""
Functions that can be used in measurements within the QTMlab framework.

Available functions:
    move(device, variable, setpoint, rate)
    measure()
    sweep(device, variable, start, stop, rate, npoints, filename, sweepdev, scale='lin')
    waitfor(device, variable, setpoint, threshold=0.05, tmin=60)
    record(dt, npoints, filename)
    record_until(dt, filename, device, variable, operator, value, maxnpoints)
    multisweep(sweep_list, npoints, filename)
    megasweep(device1, variable1, start1, stop1, rate1, npoints1, device2, variable2, start2, stop2, rate2, npoints2, filename, sweepdev1, sweepdev2, mode='standard', scale='lin')
    multimegasweep(sweep_list1, sweep_list2, npoints1, npoints2, filename)
    snapshot()
    scan_gpib()

Version 2.7.8 (2024-01-03)

Contributors:
-- University of Twente --
Daan Wielens
Joris Voerman
Tjerk Reintsema
Chuan Li
"""
import time
import numpy as np
import os
import math
from datetime import datetime

print('QTMtoolbox version 2.7.6 (2023-10-27)')
print('----------------------------------------------------------------------')

meas_dict = {}

# Global settings
dt = 0.02           # Move timestep [s]
dtw = 1             # Wait time before measurement [s]
samplename = None

# Create Data directory
if not os.path.isdir('Data'):
    os.mkdir('Data')

# Filename checker
def checkfname(filename):
    """
    This function checks if the to-be-created measurement file already exists.
    If so, it appends a number. For all successive existing (numbered) files,
    it raises the counter
    ----------
    New: the filename checker also verifies that the user provides a valid sample identifier
    so that the data is stored in a correct folder that complies with the
    data management plan.
    """
        
    if not samplename:
        raise ValueError('No sample identifier was provided. Please provide a sample identifier in the header of your measurement script.')
    else:
        sampledate = samplename.split('_')[0]
        try:
            dt_obj = datetime.strptime(sampledate, '%Y-%m-%d')
            # If the sample date is OK, check/create the folder for data storage
            if not os.path.isdir('Data/' + samplename):
                os.mkdir('Data/' + samplename)
        except Exception:
            raise ValueError('The sample identifier should have the following format: YYYY-MM-DD_<Sample-name>.')
     
    append_no = 0;
    new_filename = 'Data/' + samplename + '/' + filename
    while os.path.isfile(new_filename):
        append_no += 1 #Count the number of times the file already existed
        new_filename = new_filename.split('.')
        if append_no == 1: #The first time the program finds the unedited filename. We save it as the base
            new_filename_base = new_filename[0]
        new_filename = new_filename_base + '_' + str(append_no) +'.' + new_filename[1] #add "_N" to the filename where N is the number of loop iterations
        if os.path.isfile(new_filename) == False: #Only when the newly created filename doesn't exist: inform the user. The whileloop stops.
            print('<!> The file already exists. Filename changed to: \n    ' + new_filename)
    return(new_filename)

def move(device, variable, setpoint, rate, silent=False):
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

        #Convert rate per second to rate per minute (ips rate is in T/m)
        ratepm = round(rate * 60, 3)
        if ratepm >= 0.4:
            ratepm = 0.4
        # Don't put rate to zero if move setpoint == current value
        if ratepm == 0:
            ratepm = 0.1

        write_rate = getattr(device, 'write_rate')
        write_rate(ratepm)

        # Magnet's precision = 0.0001, so round setpoint before sending the value
        setpoint = round(setpoint, 4)
        write_command = getattr(device, 'write_' + variable)
        write_command(setpoint)

        # Check if the magnet is really at its setpoint, as the device is very slow
        reached = False
        cntr = 0
        while not reached:
            time.sleep(0.2)
            cur_val = float(read_command())
            if round(cur_val, 4) == round(setpoint, 4):
                reached = True
            else:
                cntr += 1
            # If the device is still not there, send the setpoint again
            if cntr == 5:
                time.sleep(0.2)
                write_command(setpoint)
        
        return

    #---------------------------------------------------------------------------

    # Oxford MercuryiPS Controller - alternative approach
    """
    Since the VRM (even when operated over GPIB/ethernet) also does not move to
    setpoints instantly, we implement a similar move command as we did for the
    ips120 power supply.
    Here, we calculate the rate and send this rate and the new setpoint to the
    power supply. We then check whether the magnet's state is "Moving" (i.e. at
    least one of the magnet's axes' state is RTOS (ramp to setpoint) or whether
    the state is "Hold" - only if the state is "Hold", the move command is finished).

    Sometimes, the magnet does not move correctly, so when it says RTOS but is
    not changing its setpoint, we set the magnet to HOLD and then try again. This
    is not very nice, but it circumvents the issues for the moment.

    Currently, one can only move fvalueX, fvalueY, fvalueZ, but not "vector".
    """
    #---------------------------------------------------------------------------
    devtype = str(type(device))[1:-1].split('.')[-1].strip("'")
    if devtype == 'MercuryiPS':
        read_command = getattr(device, 'read_' + variable)
        cur_val = float(read_command())

        ratepm = round(rate * 60, 3)
        if ratepm >= 0.2:
            ratepm = 0.2
        if ratepm == 0:
            ratepm = 0.1

        # This line really only works for fvalue{X,Y,Z}
        write_rate = getattr(device, 'write_rate' + variable[-1])
        write_rate(ratepm)

        write_command = getattr(device, 'write_' + variable)
        write_command(setpoint)

        #Check if the magnet reached its setpoint
        reached = False
        cntr = 0 # Initialise counter
        while not reached:
            time.sleep(0.5)
            state_command = getattr(device, 'read_status')
            prev_val = float(read_command())
            cur_state = state_command()
            # Check if magnet is moving (RTOS) or holding (HOLD)
            if cur_state == 'HOLD':
                # Check if field value is same as setpoint (within margin because
                # of the fluctuations in the given value)
                new_val = float(read_command())
                if abs(new_val - setpoint) < 1E-4:
                    reached = True
                    time.sleep(1)
            else:
                time.sleep(0.5)
                cntr += 1
                new_val = float(read_command())
                if abs(new_val - prev_val) < 1E-4 and cntr == 10:
                    cntr = 0
                    hold_command = getattr(device, 'hold')
                    hold_command()
                    time.sleep(0.5)
                    write_command(setpoint)
                    print('   Mercury iPS: performed "HOLD / RTOS" sequence.')
                else:
                    prev_val = new_val
                    
        return

    #---------------------------------------------------------------------------

    # Keithley 2450 SourceMeter
    """
    The Keithley 2450 SourceMeter is also a 'slow' device which can't keep up 
    with the current poll rate of 20 ms. We therefore incorporate a separate move
    function for the device.
    For well-documented code, please check the "Devices that can apply a setpoint instantly",
    as this code is derived from there.
    """
    if device.type == 'Keithley 2450 SourceMeter':
        dtK = 0.1
        read_command = getattr(device, 'read_' + variable)
        cur_val = float(read_command())
        time.sleep(dtK)
        Dt = abs(setpoint - cur_val) / (rate * 2) # Rate doubles, because we also wait for an extra read session
        nSteps = int(round(Dt / dtK))
        if nSteps != 0:
            move_curve = np.linspace(cur_val, setpoint, nSteps)
            for i in range(nSteps):
                if not silent:
                    cur_str = convertUnits(cur_val)
                    set_str = convertUnits(setpoint) 
                    print(end='\r')
                    print(('Setpoint: ' + set_str.ljust(8) + ' | Current value: ' + cur_str.ljust(8)).ljust(80), end='\r')
                    # Apply setpoint
                    write_command = getattr(device, 'write_' + variable)
                    write_command(move_curve[i])
                    time.sleep(dtK)
                    cur_val = read_command()
                    time.sleep(dtK)
        else:
            write_command = getattr(device, 'write_' + variable)
            write_command(setpoint)
        if not silent:    
            print('    ' + device.__class__.__name__ + '.' + variable + ' has moved to its setpoint.')
        return

    # Devices that can apply a setpoint instantly
    """
    The script below applies to most devices, which can apply a given setpoint
    instantly. Here, we can not supply a 'rate' to the device, but we create
    a linspace of setpoints and push them to the device at a regular interval.
    """

    # Get current Value
    read_command = getattr(device, 'read_' + variable)
    cur_val = float(read_command())
    
    # Determine number of steps
    Dt = abs(setpoint - cur_val) / rate
    nSteps = int(round(Dt / dt))
    # Only create linspace and move in steps when nSteps > 0
    if nSteps != 0:
        # Create list of setpoints and change setpoint by looping through array
        move_curve = np.linspace(cur_val, setpoint, nSteps)
        
        for i in range(nSteps):
            write_command = getattr(device, 'write_' + variable)
            write_command(move_curve[i])
            time.sleep(dt)
            if not silent:
                cur_str = convertUnits(move_curve[i])
                set_str = convertUnits(setpoint) 
                print(end='\r')
                print((('    ' + device.__class__.__name__ + '.' + variable).ljust(20) + ' | Setpoint: ' + set_str.ljust(8) + ' | Current value: ' + cur_str.ljust(8)).ljust(80), end='\r')
    
    # Always finish with writing the actual setpoint
    write_command = getattr(device, 'write_' + variable)
    write_command(setpoint)
    if not silent:
        print(end='\r')

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


def sweep(device, variable, start, stop, rate, npoints, filename, sweepdev, md=None, scale='lin'):
    """
    The sweep command sweeps the <variable> of <device>, from <start> to <stop>.
    Sweeping is done at <rate> and <npoints> are recorded to a datafile saved
    as <filename>.
    For measurements, the 'measurement dictionary', meas_dict, is used.
    """
    print('Starting a sweep of "' + sweepdev + '" from ' + str(start) + ' to ' + str(stop) + ' in ' + str(npoints) + ' ('+ str(scale) + ' spacing)' +' steps with rate ' + str(rate) + '.')
    print('----------------------------------------------------------------------')
    
    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    # Initialise datafile
    filename = checkfname(filename)

    # Create sweep_curve - this piece of code has moved up to make sure that IVVI corrections still end up in the header of the file.
    if scale == 'lin':
        sweep_curve = np.linspace(start, stop, npoints)
    if scale == 'log':
        sweep_curve = np.logspace(np.log10(start), np.log10(stop), npoints)
    
    # IVVI DAC discretization (for explanation, see DACsyncing below / Manual.pdf)
    if scale == 'IVVI':
        sweep_curve, start, stop, npoints = DACsyncing(start, stop, npoints) 

    # Create header
    header = sweepdev
    # The string 'setget' contains a "s" when the column is set during the measurement (i.e. a setpoint),
    # and it is a "g" when it retrieved (get) during the measurement.
    setget = 's'
    # Add device of 'meas_list'
    for dev in md:
        header = header + ', ' + dev
        setget = setget + 'g'
    # Write header to file
    with open(filename, 'w') as file:
        dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        file.write(dtm + '|' + setget + '\n')
        swcmd = 'sweep of ' + sweepdev  + ' from ' + str(start) + ' to ' + str(stop) + ' in ' + str(npoints) + ' steps ('+ str(scale) + ' spacing)' +' with rate ' + str(rate)
        file.write(swcmd + '\n')
        file.write(header + '\n')

    # Move to initial value
    print('Moving to the initial value...')
    move(device, variable, start, rate)

    print('Starting to sweep.')
    timer = []
    ETA = 0
    # Perform sweep
    for i in range(npoints):
        t_start = time.time()
        if len(timer) > 0:
            ETA = np.mean(timer) * (npoints - i) + t_start
            ETAstr = datetime.fromtimestamp(ETA).strftime('%d-%m-%Y %H:%M:%S')
        # Move to measurement value
        '''
        To make sure that every print statement is completely overwritten, pad with at least 5 extra spaces (in case the setpoint is a 5-digit value).
        In addition, pretty format small values.
        '''
        
        cur_var = sweep_curve[i]
        var_str = convertUnits(cur_var)
                    
        print(end='\r')
        print(('    Setpoint: ' + var_str.ljust(10) + ' | Moving to setpoint...').ljust(80), end='\r')
        if len(timer) > 0:
            print(end='\r')
            print(('    Setpoint: ' + var_str.ljust(10) + ' | Moving to setpoint... | Finished at: ' + ETAstr).ljust(80), end='\r')
        move(device, variable, sweep_curve[i], rate, silent=True)
        # Wait, then measure
        print(end='\r')
        print(('    Setpoint: ' + var_str.ljust(10) + ' | Measuring...         ').ljust(80), end='\r')
        if len(timer) > 0:
            print(end='\r')
            print(('    Setpoint: ' + var_str.ljust(10) + ' | Measuring...          | Finished at: ' + ETAstr).ljust(80), end='\r')
        time.sleep(dtw)
        data = np.hstack((sweep_curve[i], measure()))

        # Add data to file
        datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
        with open(filename, 'a') as file:
            file.write(datastr + '\n')
        t_end = time.time()
        timer.append(t_end - t_start)
    print('\nSweep finished.')

def waitfor(device, variable, setpoint, threshold=0.05, tmin=60):
    """
    The waitfor command waits until <variable> of <device> reached
    <setpoint> within +/- <threshold> for at least <tmin>.
    Note: <tmin> is in seconds.
    """
    print('Waiting for "'  + variable + '" to be within ' + str(setpoint) + ' +/- ' + str(threshold) + ' for at least ' + str(tmin) + ' seconds.')
    print('----------------------------------------------------------------------')
    stable = False
    t_stable = 0
    while not stable:
        # Read value
        read_command = getattr(device, 'read_' + variable)
        cur_val = float(read_command())
        var_str = convertUnits(cur_val)
        # Determine if value within threshold
        if abs(cur_val - setpoint) <= threshold:
            # Add time to counter
            print(end='\r')
            print(('    Current value: ' + var_str.ljust(10) + ' | Value within threshold, waiting (' + str(t_stable) + ' s)...         ').ljust(80), end='\r')
            t_stable += 5
        else:
            # Reset counter
            t_stable = 0
            print(end='\r')
            print(('    Current value: ' + var_str.ljust(10) + ' | Value outside threshold...         ').ljust(80), end='\r')
        time.sleep(5)
        # Check if t_stable > tmin
        if t_stable >= tmin:
            stable = True
            print(end='\r')
            print(('    Current value: ' + var_str.ljust(10) + ' | Value within threshold, waiting (' + str(t_stable) + ' s)...         ').ljust(80), end='\r')
            print('\nThe device is stable.')

def record(dt, npoints, filename, append=False, md=None, silent=False):
    """
    The record command records data with a time interval of <dt> seconds. It
    will record data for a number of <npoints> and store it in <filename>.
    """
    print('Recording data with a time interval of ' + str(dt) + ' seconds for (up to) ' + str(npoints) + ' points. Hit <Ctrl+C> to abort.')
    print('----------------------------------------------------------------------')
    if silent:
        print('   Silent mode enabled. Measurements will not be logged in the console.')

    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    if append == False:
        # Initialise datafile
        filename = checkfname(filename)

        # Build header
        header = 'time'
        setget = 's'
        for dev in md:
            header = header + ', ' + dev
            setget = setget + 'g'
        # Write header to file
        with open(filename, 'w') as file:
            dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            file.write(dtm + '|' + setget + '\n')
            swcmd = 'record data with dt = ' + str(dt) + ' s for max ' + str(npoints) + ' datapoints'
            file.write(swcmd + '\n')
            file.write(header + '\n')

    # Perform record
    for i in range(npoints):
        if not silent:
            print(end='\r')
            print('   t = ' + (str(np.round(i*dt, 2)) + ' s').ljust(10) + ' | Measuring... ', end='\r')
        data = measure()
        datastr = (str(i*dt) + ', ' + np.array2string(data, separator=', ')[1:-1]).replace('\n', '')
        if append == False:
            with open(filename, 'a') as file:
                file.write(datastr + '\n')
        elif append == True:
            with open('Data//' + samplename + '//' + filename, 'a') as file:
                file.write(datastr + '\n')
        time.sleep(dt)

def record_until(dt, filename, device, variable, operator, value, maxnpoints, md=None):
    """
    The record command records data with a time interval of <dt> seconds. It
    will record data for a number of <npoints> and store it in <filename>.
    """
    print('Recording data until ' + variable + ' ' + operator + ' ' + str(value) + '.')
    print('----------------------------------------------------------------------')
    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict
        
    # Initialise datafile
    filename = checkfname(filename)

    # Build header
    header = 'time'
    setget = 's'
    for dev in md:
        header = header + ', ' + dev
        setget = setget + 'g'
    # Write header to file
    with open(filename, 'w') as file:
        dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        file.write(dtm + '|' + setget + '\n')
        swcmd = 'record_until data with dt = ' + str(dt) + ' s for max ' + str(maxnpoints) + ' datapoints'
        file.write(swcmd + '\n')
        file.write(header + '\n')
    
    reached = False 
    i = 0      
    # Perform record
    while not reached:
        print(end='\r')
        print('Performing measurement at t = ' + str(i*dt) + ' s.', end='\r')
        data = measure()
        datastr = (str(i*dt) + ', ' + np.array2string(data, separator=', ')[1:-1]).replace('\n', '')
        with open(filename, 'a') as file:
            file.write(datastr + '\n')
        i += 1
        time.sleep(dt)
        
        # Check for given criterion
        read_command = getattr(device, 'read_' + variable)
        cur_val = float(read_command())
        
        if operator in ['larger', '>']:
            if cur_val > value:
                reached = True
        if operator in ['smaller', '<']:
            if cur_val < value:
                reached = True
        if operator in ['equal', '=', '==']:
            if cur_val == value:
                reached = True
        if i > maxnpoints:
            reached = True        
        
def multisweep(sweep_list, npoints, filename, md=None):
    """
    The multisweep command sweeps multiple variables simultaneously. The sweep list contains
    all variables, along with their parameters, also stored in a list. An example could be

        sweep_list = [
                        [dev1, var1, start1, stop1, rate1, sweepdev1],
                        [dev2, var2, start2, stop2, rate2, sweepdev2],
                        [dev3, var3, start3, stop3, rate3, sweepdev3],
                        ....
                     ]

    The command moves all devices to their respective setpoints, takes a single measurement
    and then moves all devices again to their next setpoint.
    """
    print('Starting a multisweep.')
    print('----------------------------------------------------------------------')

    if md is None:
        md = meas_dict

    filename = checkfname(filename)

    header = ''
    setget = ''
    for sweepvar in sweep_list:
        if header == '':
            header = sweepvar[5]
            setget = 's'
        else:
            header = header + ', ' + sweepvar[5]
            setget = setget + 's'
    for dev in md:
        header = header + ', ' + dev
        setget = setget + 'g'
    with open(filename, 'w') as file:
        dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        file.write(dtm + '|' + setget + '\n')
        swcmd = 'multisweep scan' # Implement this!
        file.write(swcmd + '\n')
        file.write(header + '\n')

    # Move variables to initial value
    for sweepvar in sweep_list:
        move(sweepvar[0], sweepvar[1], sweepvar[2], sweepvar[4])

    # Create sweep curves
    sweep_curve_list = []
    for sweepvar in sweep_list:
        sweep_curve = np.linspace(sweepvar[2], sweepvar[3], npoints)
        sweep_curve_list.append(sweep_curve)

    # Perform sweep
    timer = []
    for i in range(npoints):
        t_start = time.time()
        if len(timer) > 0:
            ETA = np.mean(timer) * (npoints - i) + t_start
            ETAstr = datetime.fromtimestamp(ETA).strftime('%d-%m-%Y %H:%M:%S')
        # Move to the measurement values
        var_str = convertUnits(sweep_curve_list[0][i])
        print(end='\r')
        print(('    1st setpoint: ' + var_str.ljust(10) + ' | Moving to setpoint...').ljust(80), end='\r')
        if len(timer) > 0:
            print(end='\r')
            print(('    1st setpoint: ' + var_str.ljust(10) + ' | Moving to setpoint... | Finished at: ' + ETAstr).ljust(80), end='\r')

        for j in range(len(sweep_list)):
            move(sweep_list[j][0], sweep_list[j][1], sweep_curve_list[j][i], sweep_list[j][4], silent=True)
        # Wait, then measure
        print(end='\r')
        print(('    1st setpoint: ' + var_str.ljust(10) + ' | Measuring...         ').ljust(80), end='\r')
        if len(timer) > 0:
            print(end='\r')
            print(('    1st setpoint: ' + var_str.ljust(10) + ' | Measuring...          | Finished at: ' + ETAstr).ljust(80), end='\r')
        time.sleep(dtw)
        data_setp = np.array([])
        for j in range(len(sweep_list)):
            data_setp = np.append(data_setp, sweep_curve_list[j][i])
        data = np.hstack((data_setp, measure()))

        # Add data to file
        datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
        with open(filename, 'a') as file:
            file.write(datastr + '\n')
        t_end = time.time()
        timer.append(t_end - t_start)
    print('\nMultisweep finished.')

def megasweep(device1, variable1, start1, stop1, rate1, npoints1, device2, variable2, start2, stop2, rate2, npoints2, filename, sweepdev1, sweepdev2, mode='standard', scale='lin', md=None):
    """
    The megasweep command sweeps two variables. Variable 1 is the "slow" variable.
    For every datapoint of variable 1, a sweep of variable 2 ("fast" variable) is performed.
    The syntax for both variables is <device>, <variable>, <start>, <stop>, <rate>, <npoints>.
    For measurements, the 'measurement dictionary', meas_dict, is used.
    If the scale is changed from 'lin' to 'IVVI', the DAC syncing (see Manual.pdf on 'sweep') will be enabled for the fast axis (variable 2).
    """
    print('Starting a "' + mode + '" megasweep of the following variables:')
    print('1: "' + variable1 + '" from ' + str(start1) + ' to ' + str(stop1) + ' in ' + str(npoints1) + ' steps with rate ' + str(rate1))
    print('2: "' + variable2 + '" from ' + str(start2) + ' to ' + str(stop2) + ' in ' + str(npoints2) + ' steps with rate ' + str(rate2))
    print('----------------------------------------------------------------------')

    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    # Initialise datafile
    filename = checkfname(filename)

    # Move to initial value
    print('Moving variable1 to the initial value...')
    move(device1, variable1, start1, rate1)
    print('Moving variable2 to the initial value...')
    move(device2, variable2, start2, rate2)

    # Create sweep_curve
    sweep_curve1 = np.linspace(start1, stop1, npoints1)
    if scale == 'IVVI':
        sweep_curve2, start2, stop2, npoints2 = DACsyncing(start2, stop2, npoints2)
    else:
        sweep_curve2 = np.linspace(start2, stop2, npoints2)
        
    # Create header
    header = sweepdev1 + ', ' + sweepdev2
    setget = 'ss'
    # Add device of 'meas_list'
    for dev in md:
        header = header + ', ' + dev
        setget = setget + 'g'
    # Write header to file
    with open(filename, 'w') as file:
        dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        file.write(dtm + '|' + setget + '\n')
        swcmd = 'Megasweep of (1)' + sweepdev1  + ' from ' + str(start1) + ' to ' + str(stop1) + ' in ' + str(npoints1)  +' steps with rate ' + str(rate1) + 'and (2) ' + sweepdev2  + ' from ' + str(start2) + ' to ' + str(stop2) + ' in ' + str(npoints2)  +' steps with rate ' + str(rate2)
        file.write(swcmd + '\n')
        file.write(header + '\n')

    if mode=='standard':
        timer_slow = []
        timer_fast = []
        for i in range(npoints1):
            t_slow_start = time.time()
            # Move device1 to value1
            move(device1, variable1, sweep_curve1[i], rate1, silent=True)
            # Sweep variable2
            t_slow_end = time.time() # This times the duration of a 'move' of the slow device
            timer_slow.append(t_slow_end - t_slow_start)
            for j in range(npoints2):
                t_fast_start = time.time()
                if len(timer_fast) > 0:
                    ETA = np.mean(timer_slow) * (npoints1 - i) + np.mean(timer_fast) * (npoints2 - 1) + np.mean(timer_fast) * (npoints1-i) * npoints2 + t_fast_start
                    ETAstr = datetime.fromtimestamp(ETA).strftime('%d-%m-%Y %H:%M:%S')
                # Move device2 to measurement value
                move(device2, variable2, sweep_curve2[j], rate2, silent=True)
                setp1_str = convertUnits(sweep_curve1[i])
                setp2_str = convertUnits(sweep_curve2[j])                
                # Wait, then measure                
                print(end='\r')
                print(('    (1): ' + setp1_str.ljust(10) + ' | (2): ' + setp2_str.ljust(10) + ' | Moving to setpoint...').ljust(100), end='\r')
                if len(timer_fast) > 0:
                    print(end='\r')
                    print(('    (1): ' + setp1_str.ljust(10) + ' | (2): ' + setp2_str.ljust(10) + ' | Moving to setpoint... | Finished at: ' + ETAstr).ljust(100), end='\r')                
                time.sleep(dtw)
                print(end='\r')
                print(('    (1): ' + setp1_str.ljust(10) + ' | (2): ' + setp2_str.ljust(10) + ' | Measuring...         ').ljust(100), end='\r')
                if len(timer_fast) > 0:
                    print(end='\r')
                    print(('    (1): ' + setp1_str.ljust(10) + ' | (2): ' + setp2_str.ljust(10) + ' | Measuring...          | Finished at: ' + ETAstr).ljust(100), end='\r')
                data = np.hstack((sweep_curve1[i], sweep_curve2[j], measure()))

                #Add data to file
                datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
                with open(filename, 'a') as file:
                    file.write(datastr + '\n')
                t_fast_end = time.time()
                timer_fast.append(t_fast_end - t_fast_start)
        print('\nMegasweep finished.')

    elif mode=='updown':
        for i in range(npoints1):
            # Move device1 to value1
            print('Measuring for device 1 at {}'.format(sweep_curve1[i]))
            move(device1, variable1, sweep_curve1[i], rate1)
            # Sweep variable2
            #   We create a linspace that replaces the range: the linspace goes back and forth
            sweep_curve2ud = np.hstack((sweep_curve2, sweep_curve2[::-1]))
            for j in range(npoints2*2):
                # Move device2 to measurement value
                print('   Sweeping to: {}'.format(sweep_curve2ud[j]))
                move(device2, variable2, sweep_curve2ud[j], rate2)
                # Wait, then measure
                print('      Waiting for measurement...')
                time.sleep(dtw)
                print('      Performing measurement.')
                data = np.hstack((sweep_curve1[i], sweep_curve2ud[j], measure()))

                #Add data to file
                datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
                with open(filename, 'a') as file:
                    file.write(datastr + '\n')

    elif mode=='updownsplit':
        filename2 = filename[:-4] + '_dir2.csv'
        with open(filename2, 'w') as file:
            dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            file.write(dtm + '\n')
            swcmd = 'Megasweep of (1)' + sweepdev1  + ' from ' + str(start1) + ' to ' + str(stop1) + ' in ' + str(npoints1)  +' steps with rate ' + str(rate1) + 'and (2) ' + sweepdev2  + ' from ' + str(start2) + ' to ' + str(stop2) + ' in ' + str(npoints2)  +' steps with rate ' + str(rate2)
            file.write(swcmd + '\n')
            file.write(header + '\n')
        
        for i in range(npoints1):
            # Move device1 to value1
            print('Measuring for device 1 at {}'.format(sweep_curve1[i]))
            move(device1, variable1, sweep_curve1[i], rate1)
            time.sleep(5*dtw)
            # Sweep variable2
            #   We create a linspace that replaces the range: the linspace goes back and forth
            sweep_curve2ud = np.hstack((sweep_curve2, sweep_curve2[::-1]))
            for j in range(npoints2*2):
                # Move device2 to measurement value
                print('   Sweeping to: {}'.format(sweep_curve2ud[j]))
                move(device2, variable2, sweep_curve2ud[j], rate2)
                # Wait, then measure
                print('      Waiting for measurement...')
                time.sleep(dtw)
                print('      Performing measurement.')
                data = np.hstack((sweep_curve1[i], sweep_curve2ud[j], measure()))
                
                #Add data to file
                # We split the file in the "up" and "down" part of the updown sweep
                datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
                if j < npoints2:
                    with open(filename, 'a') as file:
                        file.write(datastr + '\n')
                else:
                    with open(filename2, 'a') as file:
                        file.write(datastr + '\n')
                    
    elif mode=='serpentine':
        z = 0
        for i in range(npoints1):
            z += 1
            # Move device1 to value1
            print('Measuring for device 1 at {}'.format(sweep_curve1[i]))
            move(device1, variable1, sweep_curve1[i], rate1)
            # Sweep variable2
            if (z % 2) == 1:
                for j in range(npoints2):
                    # Move device2 to measurement value
                    print('   Sweeping to: {}'.format(sweep_curve2[j]))
                    move(device2, variable2, sweep_curve2[j], rate2)
                    # Wait, then measure
                    print('      Waiting for measurement...')
                    time.sleep(dtw)
                    print('      Performing measurement.')
                    data = np.hstack((sweep_curve1[i], sweep_curve2[j], measure()))

                    #Add data to file
                    datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
                    with open(filename, 'a') as file:
                        file.write(datastr + '\n')

            if (z % 2) == 0:
                for j in range(npoints2):
                    # Move device2 to measurement value
                    #  Here, we take -j to reverse the direction of the sweep.
                    print('   Sweeping to: {}'.format(sweep_curve2[-(j+1)]))
                    move(device2, variable2, sweep_curve2[-(j+1)], rate2)
                    # Wait, then measure
                    print('      Waiting for measurement...')
                    time.sleep(dtw)
                    print('      Performing measurement.')
                    data = np.hstack((sweep_curve1[i], sweep_curve2[-(j+1)], measure()))

                    #Add data to file
                    datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
                    with open(filename, 'a') as file:
                        file.write(datastr + '\n')


def multimegasweep(sweep_list1, sweep_list2, npoints1, npoints2, filename, md=None):
    """
    The multimegasweep combines the two-axis measurements of the megasweep with the possibility
    of the multisweep to sweep multiple variables simultaneously. Both megasweep axes hold a
    sweep_list and can thus in principle have multiple variables that can be changed.

    An example sweep_list is:

        sweep_list = [
                        [dev1, var1, start1, stop1, rate1, sweepdev1],
                        [dev2, var2, start2, stop2, rate2, sweepdev2],
                        [dev3, var3, start3, stop3, rate3, sweepdev3],
                        ....
                     ]

    Just as with the multisweep, we move all devices to their setpoint successively and then
    perform a single measurement.

    Regarding the megasweep: only the 'standard' mode is implemented below.
    """
    print('Starting a multimegasweep.')

    if md is None:
        md = meas_dict

    filename = checkfname(filename)

    # Construct header
    header = ''
    setget = ''
    for sweepvar in sweep_list1:
        if header == '':
            header = sweepvar[5]
            setget = 's'
        else:
            header = header + ', ' + sweepvar[5]
            setget = setget + 's'
    for sweepvar in sweep_list2:
        header = header + ', ' + sweepvar[5]
        setget = setget + 's'
    for dev in md:
        header = header + ', ' + dev
        setget = setget + 'g'
    with open(filename, 'w') as file:
        dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        file.write(dtm + '|' + setget + '\n')
        swcmd = 'multimegasweep scan' # Implement this!
        file.write(swcmd + '\n')
        file.write(header + '\n')

    # Move variables to initial value
    print('Moving variables of sweep_list1 to their initial values...')
    for sweepvar in sweep_list1:
        move(sweepvar[0], sweepvar[1], sweepvar[2], sweepvar[4])
    print('Moving variables of sweep_list2 to their initial values...')
    for sweepvar in sweep_list2:
        move(sweepvar[0], sweepvar[1], sweepvar[2], sweepvar[4])

    # Create sweep curves
    sweep_curve_list1 = []
    for sweepvar in sweep_list1:
        sweep_curve = np.linspace(sweepvar[2], sweepvar[3], npoints1)
        sweep_curve_list1.append(sweep_curve)
    sweep_curve_list2 = []
    for sweepvar in sweep_list2:
        sweep_curve = np.linspace(sweepvar[2], sweepvar[3], npoints2)
        sweep_curve_list2.append(sweep_curve)

    # --- Perform megasweep ---
    timer_slow = []
    timer_fast = []
    # Sweep slow axis
    for i in range(npoints1):
        t_slow_start = time.time()
        # Move to the measurement values
        for j in range(len(sweep_list1)):
            move(sweep_list1[j][0], sweep_list1[j][1], sweep_curve_list1[j][i], sweep_list1[j][4], silent=True)
        t_slow_end = time.time()
        timer_slow.append(t_slow_end - t_slow_start) # This times the duration of a 'move' of all slow devices
        
        # Sweep fast axis
        t_fast_start = time.time()
        if len(timer_fast) > 0:
            ETA = np.mean(timer_slow) * (npoints1 - i) + np.mean(timer_fast) * (npoints2 - 1) + np.mean(timer_fast) * (npoints1-i) * npoints2 + t_fast_start
            ETAstr = datetime.fromtimestamp(ETA).strftime('%d-%m-%Y %H:%M:%S')
        for k in range(npoints2):
            # Move to the measurement values
            for l in range(len(sweep_list2)):
                move(sweep_list2[l][0], sweep_list2[l][1], sweep_curve_list2[l][k], sweep_list2[l][4], silent=True)
                
            setp1_str = convertUnits(sweep_curve_list1[0][i])
            setp2_str = convertUnits(sweep_curve_list2[0][k]) 
            # Wait, then measure                
            print(end='\r')
            print(('    (1.1): ' + setp1_str.ljust(10) + ' | (2.1): ' + setp2_str.ljust(10) + ' | Moving to setpoint...').ljust(100), end='\r')
            if len(timer_fast) > 0:
                print(end='\r')
                print(('    (1.1): ' + setp1_str.ljust(10) + ' | (2.1): ' + setp2_str.ljust(10) + ' | Moving to setpoint... | Finished at: ' + ETAstr).ljust(100), end='\r')                
            time.sleep(dtw)
            print(end='\r')
            print(('    (1.1): ' + setp1_str.ljust(10) + ' | (2.1): ' + setp2_str.ljust(10) + ' | Measuring...         ').ljust(100), end='\r')
            if len(timer_fast) > 0:
                print(end='\r')
                print(('    (1.1): ' + setp1_str.ljust(10) + ' | (2.1): ' + setp2_str.ljust(10) + ' | Measuring...          | Finished at: ' + ETAstr).ljust(100), end='\r')
                        
            data_setp = np.array([])
            for m in range(len(sweep_list1)):
                data_setp = np.append(data_setp, sweep_curve_list1[m][i])
            for n in range(len(sweep_list2)):
                data_setp = np.append(data_setp, sweep_curve_list2[n][k])
            data = np.hstack((data_setp, measure()))

            #Add data to file
            datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
            with open(filename, 'a') as file:
                file.write(datastr + '\n')
        t_fast_end = time.time()
        timer_fast.append(t_fast_end - t_fast_start)
    print('\nMultimegasweep finished.')

def megalistsweep(sweep_list, device2, variable2, start2, stop2, rate2, npoints2, filename, sweepdev2, mode='standard', md=None):
    """
    The megalistsweep command sweeps multiple variables simultaneously. The sweep list contains
    all variables, along with their parameters, also stored in a list. An example could be

        sweep_list = [
                        [dev1, var1, <list of points>, rate1, sweepdev1],
                        [dev2, var2, <list of points>, rate2, sweepdev2],
                        [dev3, var3, <list of points>, rate3, sweepdev3],
                        ....
                     ]

    The command moves all devices to their respective setpoints, takes a single measurement
    and then moves all devices again to their next setpoint.
    """
    print('Starting a "' + mode + '" megalistsweep of the following variables:')
#    print('1: "' + sweeplist[0] + '" from ' + str(start1) + ' to ' + str(stop1) + ' in ' + str(npoints1) + ' steps with rate ' + str(rate1))
    print('2: "' + variable2 + '" from ' + str(start2) + ' to ' + str(stop2) + ' in ' + str(npoints2) + ' steps with rate ' + str(rate2))

    # Trick to make sure that dictionary loading is handled properly at startup
    print('Starting a megalistsweep.')

    if md is None:
        md = meas_dict
        
    filename = checkfname(filename)

    header = ''
    for sweepvar in sweep_list:
        if header == '':
            header = sweepvar[4]
        else:
            header = header + ', ' + sweepvar[4]
    header = header+  ', '+ sweepdev2

    for dev in md:
        header = header + ', ' + dev
    with open(filename, 'w') as file:
        dtm = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        file.write(dtm + '\n')
        swcmd = 'multilistsweep scan' # Implement this!
        file.write(swcmd + '\n')
        file.write(header + '\n')

    # Move variables to initial value
    for sweepvar in sweep_list:
        move(sweepvar[0], sweepvar[1], sweepvar[2][0], sweepvar[3])

    # Create sweep curves
    sweep_curve_list = []
    for sweepvar in sweep_list:
        sweep_curve = sweepvar[2]
        sweep_curve_list.append(sweep_curve)
        npoints = len(sweep_curve)

    sweep_curve2 = np.linspace(start2, stop2, npoints2)
    if mode=='standard':
        for i in range(npoints):
            # Move to the measurement values
            print('   Sweeping all variables. First variable to: {}'.format(sweep_curve_list[0][i]))
            for j in range(len(sweep_list)):
                move(sweep_list[j][0], sweep_list[j][1], sweep_curve_list[j][i], sweep_list[j][3])
            # Wait, then measure
            print('      Waiting for measurement...')
            time.sleep(dtw)
            print('      Performing measurement.')
            data_setp = np.array([])
            for j in range(len(sweep_list)):
                data_setp = np.append(data_setp, sweep_curve_list[j][i])
            
            for k in range(npoints2):
                # Move device2 to measurement value
                print('   Sweeping to: {}'.format(sweep_curve2[k]))
                move(device2, variable2, sweep_curve2[k], rate2)
                # Wait, then measure
                print('      Waiting for measurement...')
                time.sleep(dtw)
                print('      Performing measurement.')
                data = np.hstack((data_setp, sweep_curve2[k], measure()))

                #Add data to file
                datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
                with open(filename, 'a') as file:
                    file.write(datastr + '\n')                
                
def generate_meas_dict(globals_dict, meas_list):
    """
    Generates meas_dict from more compact meas_list.
    When calling this function, enter globals() for the globals_dict.
    """
    meas_dict = dict()
    meas_list = meas_list.replace(' ','').split(',')
    for devvar in meas_list:
        split = devvar.split('.')
        devstring = split[0]
        var = split[1]
        dev = globals_dict[devstring]
        meas_dict[devvar] = {'dev': dev,
                             'var': var,
                             'name': devstring}
    return meas_dict

def snapshot(md=None):
    """
    Stores a snapshot of all the measurement setup's parameters. For every 
    unique device in the measurement dictionary (meas_dict), all attributes
    that contain "_read" will be measured and stored in a single text file.
    This includes "_read" commands that are not present in the meas_dict itself.
    """
    if md is None:
        md = meas_dict
    
    # Get list with unique devices
    dev_obj_list = [] 
    dev_name_list = []               
    for device in md:      
        if md[device]['dev'] not in dev_obj_list:
            dev_obj_list.append(md[device]['dev'])
            dev_name_list.append(md[device]['name'])
    
    # Create file
    timestamp = datetime.now().strftime('%Y-%d-%m-%H%M%S')
    with open(checkfname(timestamp + 'Snapshot.txt'), 'w') as file:
        
        # For each device, get all "read_" attributes
        for [devobj, devname]  in zip(dev_obj_list, dev_name_list):
            attr_list = [attr for attr in dir(devobj) if 'read_' in attr]
            # Loop over attributes, measure property, write to file
            for attr in attr_list:
                # Skip  type objects
                if not 'auto' in attr and not 'read_dacs' in attr and attr != 'read_dac' and attr != 'read_dac_byte' and attr != 'read_conttrig':
                    meas_command = getattr(devobj, attr)
                    data = meas_command()
                    file.write(devname + '.' + attr + ': ' + str(data) + '\n')
            
def scan_gpib():
    import pyvisa as visa
    rm = visa.ResourceManager()
    devs = rm.list_resources()
    for dev in devs:
        ses = rm.open_resource(dev)
        try:
            print(dev + ' : ' + ses.query('*IDN?'))
        except Exception:
            # For Oxford iPS sources, use other query
            try:
                visa.read_termination = '\r'
                print(dev + ' : ' + ses.query('V'))
            except visa.VisaIOError as e:
                if e.abbreviation == 'VI_ERROR_TMO':
                    print(dev + ' : got VISA timeout.')
                else:
                    print(dev + ' : got VISA error.')
            except Exception:
                print(dev + ' : no info available.') 
                
def DACsyncing(start, stop, npoints):
    '''
    The DACs of the IVVI rack can be controlled by 16-bit (0...65535) values. With a range of 4 V and 65536 possible steps, every step 
    corresponds to (4 V / 65535 steps) = 61.04 uV. If you sweep with a step size of 80 uV, this means that sometimes you'll jump one 
    'dacstep', but also sometimes you'll jump two dacsteps because of the discretized nature of the DACs. 
    For IV measurements of extremely linear (flat resistance) devices, this may yield unexpected results when the resistance
    is calculated directly through numerical differentiation of the V/I. 
    
    To circumvent the issue, we convert <start> and <stop> to values that match with a dacstep. The increment (integer number of dacsteps)
    is chosen to make sure that the dac-linspace still has <npoints>, unless the increment is smaller than the dacstep, for which <npoints>
    changes to (stop-start)/dacsteps.
    
    Note: IVVI corrections are only implemented for the BIP (bipolar) polarity setting of the DAC module.
    '''
    print('<!> IVVI DAC correction is enabled for this sweep')
    # Calculate the size of one dacstep
    dac_quantum = 4 / (2**16 - 1)
    # For the 'user input' <start>, <end> and <npoints>, calculate the requested stepsize
    req_stepsize = (stop - start) / npoints
    # Compute the closest number of dacsteps, which will be the new increment
    dac_stepsize = int(round(req_stepsize / dac_quantum))
    if dac_stepsize < 1:
        dac_stepsize = 1
        print('Warning: your selected stepsize is smaller than a DAC step and thus will be converted into 1 DAC step (61.04 uV)')
    '''
    Now construct the dac-linspace: start from the middle between <start> and <stop>, take 
    the dac value closest to that. Then, given the <dac_stepsize>, move outwards from there
    until the dac value exceeds <start> (or stop). Take the last previous point as <dac_start>. 
    This ensures that the new dac values will never exceed the input values of the user.
    '''      
    # Construct dac-linspace
    dac_list = (np.arange(0, 2**16) * dac_quantum) - 2 # Bipolar list of [-2 V, 2 V]
    # Find midpoint of dac-linspace
    midpoint = (stop - start) / 2
    dac_mid_index = np.argmin(np.abs(dac_list - midpoint))
    # Keep only points of the dac_list which fulfill these two criteria:
    # - Their index is a multiple of dac_stepsize
    # - The list of the indices of dac_list intersects with dac_mid_index
    index_list = np.arange(0, 2**16, dac_stepsize)
    Found = False
    while not Found:
        if dac_mid_index in index_list:
            Found = True
        else:
            index_list += 1
    # Convert start and stop to byte values. Round so that start < dac_start and stop > dac_stop
    dac_start_index = int(np.ceil((start + 2)/dac_quantum))
    dac_stop_index = int(np.floor((stop + 2)/dac_quantum))
    # Remove all indices from index_list which are outside [dac_start_index, dac_stop_index]
    index_list = index_list[index_list > dac_start_index]
    index_list = index_list[index_list < dac_stop_index]
    # Construct voltage sweep_curve
    sweep_curve = dac_list[index_list]
    start = dac_list[dac_start_index]
    stop = dac_list[dac_stop_index]
    npoints = len(sweep_curve) 

    return sweep_curve, start, stop, npoints               
        
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Code from: https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()    
        
def convertUnits(val):
    '''
    Takes a numeric value (float) as input and provides a string with engineering suffix.
        1E-9 = 1n
        1E-6 = 1u
        1E-3 = 1m
        1E0 = 1
        1E3 = 1k
        1E6 = 1M
        1E9 = 1G
    '''
    abs_val = np.abs(val)
    # Small numbers
    if abs_val < 1:
        if abs_val < 1E-3:
            if abs_val < 1E-6:
                if abs_val == 0.0:
                    return '0'
                return str(np.round(val * 1E9, 4)) + 'n'
            return  str(np.round(val * 1E6, 4)) + 'u'
        return str(np.round(val * 1E3, 4)) + 'm'
     # Large numbers
    elif abs_val > 1E3:
        if abs_val > 1E6:
            if abs_val > 1E9:
                return str(np.round(val / 1E9, 4)) + 'G'
            return str(np.round(val / 1E6, 4)) + 'M'
        return str(np.round(val / 1E3, 4)) + 'k'
    else:
        return str(np.round(val, 4))

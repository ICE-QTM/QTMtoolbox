# -*- coding: utf-8 -*-
"""
Functions that can be used in measurements within the QTMlab framework.

Available functions:
    move(device, variable, setpoint, rate)
    measure()

Version 1.4 (2018-10-11)
Daan Wielens - PhD at ICE/QTM
University of Twente
daan@daanwielens.com
"""
import time
import numpy as np
import os
from tqdm import tqdm_gui

meas_dict = {}

# Global settings
dt = 0.02           # Move timestep [s]
dtw = 1             # Wait time before measurement [s]

# TODO: add plot labels and such
# TODO: support multiple devices/variables

# TODO: test
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
        while not reached:
            time.sleep(0.1)
            cur_val = float(read_command())
            if round(cur_val, 2) == round(setpoint, 2):
                reached = True

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
        for i in tqdm_gui(range(nSteps)):
            write_command = getattr(device, 'write_' + variable)
            write_command(move_curve[i])

            # Wait for device to reach setpoint before next move
            reached = False
            while not reached:
                time.sleep(dt)
                cur_val = float(read_command())
                if round(cur_val, 2) == move_curve[i]:
                    reached = True


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
            
# TODO: test
def sweep(device, variable, start, stop, rate, npoints, filename,
                 plot=True, sweepdev=None, md=None):
    import pyqtgraph as pg
    
    # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    # Initialise datafile and write header
    while os.path.isfile(filename):
        print('The file already exists. Appending "_1" to the filename.')
        filename = filename.split('.')
        filename = filename[0] + '_1.' + filename[1]
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
        
    # TODO: this should show a plot!
    # Move to initial value
    move(device, variable, start, rate)
    
    # Create sweep_curve
    sweep_curve = np.round(np.linspace(start, stop, npoints), 3)
    
    if plot:
        # Initialize plot
        p = pg.plot()
        p.showGrid(True, True)
        curve = p.plot()
        plotdata = []
        plottime = []
    
    i = 0
    def update():
        nonlocal curve, plotdata, i
        if i == npoints - 1:
            timer.stop()
        
        # Measure first..
        print('Performing measurement.')
        data = np.hstack((sweep_curve[i], measure()))  
        
        if plot:
            # Plot stuff
            latestData = measure()[0]
            plotdata.append(latestData)
            plottime.append(i*dtw)
            curve.setData(plottime, plotdata)
        
        # Write stuff
        datastr = np.array2string(data, separator=', ')[1:-1].replace('\n','')
        with open(filename, 'a') as file:
            file.write(datastr + '\n')
    
        # Move to measurement value
        print('Sweeping to: {}'.format(sweep_curve[i]))
        # TODO: maybe this should not show a progress thing
        move(device, variable, sweep_curve[i], rate)

        i += 1
    
    # Send a plot/write command every <dtw> seconds
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(dtw * 1000)

def waitfor(device, variable, setpoint, threshold=0.05, tmin=60):
    """
    The waitfor command waits until <variable> of <device> reached
    <setpoint> within +/- <threshold> for at least <tmin>.
    Note: <tmin> is in seconds.
    """
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

def record(dt, npoints, filename, plot=True, md=None, ):
    """
    The record command records (and by default, plots) data with a time
    interval of <dt> seconds. It will record data for a number of <npoints> and
    store it in <filename>.
    """
    import pyqtgraph as pg
    
     # Trick to make sure that dictionary loading is handled properly at startup
    if md is None:
        md = meas_dict

    # Build header
    header = 'time'
    for dev in md:
        header = header + ', ' + dev
    # Write header to file
    with open(filename, 'w') as file:
        file.write(header + '\n')
        
    if plot:
        # Initialize plot
        p = pg.plot()
        p.showGrid(True, True)
        curve = p.plot()
        plotdata = []
        plottime = []
        # TODO: should be changed when adding support for multiple vars
        for dev in md:
            var = md.get(dev).get('var')
        p.setLabel('left', text=var)
        p.setLabel('bottom', 'time')
    
    i = 0
    def update():
        nonlocal curve, plotdata, i
        if i == npoints - 1:
            timer.stop()
        
        if plot:
            # Plot stuff
            latestData = measure()[0]
            plotdata.append(latestData)
            plottime.append(i*dt)
            curve.setData(plottime, plotdata)
        
        # Write stuff
        writedata = measure()
        datastr = (str(i*dt) + ', ' + np.array2string(
                writedata, separator=', ')[1:-1]).replace('\n', '')
        with open(filename, 'a') as file:
            file.write(datastr + '\n')

        i += 1
    
    # Send a plot/write command every <dt> seconds
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(dt * 1000)
    
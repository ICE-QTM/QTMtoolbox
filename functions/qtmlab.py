# -*- coding: utf-8 -*-
"""
Functions that can be used in measurements within the QTMlab framework.

Available functions:
    move(device, variable, setpoint, rate)
    measure()
    sweep(device, variable, start, stop, rate, npoints, filename)

Version 1.51 (2019-03-12) -- Edited by Joris
Daan Wielens   - PhD at ICE/QTM - daan@daanwielens.com
Joris Voerman  - PhD at ICE/QTM - j.a.voerman@utwente.nl
University of Twente
"""
import time
import numpy as np
import os
import math
import pyqtgraph as pg

from tqdm import tqdm_gui
from tqdm import tqdm

meas_dict = {}

# Global settings
dt = 0.02           # Move timestep [s]
dtw = 1             # Wait time before measurement [s]

# Create Data directory
if not os.path.isdir('Data'):
    os.mkdir('Data')

# TODO: show values while changing
def move(device, variable, setpoint, rate, showprogress='console'):
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
    # -------------------------------------------------------------------------
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
    # -------------------------------------------------------------------------
    # Get current Value
    read_command = getattr(device, 'read_' + variable)
    cur_val = float(read_command())

    #Check sweep direction
    if cur_val > setpoint:
        direction = 'down'
    else:
        direction = 'up'

    # Determine number of steps
    Dt = abs(setpoint - cur_val) / rate
    nSteps = int(round(Dt / dt))

    if showprogress == 'gui':
        progressbar = tqdm_gui(leave=False,
                               unit='Hz',
                               unit_scale=True,
                               total=nSteps,)
    elif showprogress == 'console':
        progressbar = tqdm(total=nSteps,)

    # Only move when setpoint != curval, i.e. nSteps != 0
    if nSteps != 0:
        # Create list of setpoints and change setpoint by looping through array
        move_curve = np.round(np.linspace(cur_val, setpoint, nSteps), 2)
        for i in range(nSteps):
            write_command = getattr(device, 'write_' + variable)
            write_command(move_curve[i])

            # Wait for device to reach setpoint before next move
            reached = False
            while not reached:
                time.sleep(dt)
                cur_val = float(read_command())
                #If the current value matches the desired value at this step we move on
                if round(cur_val, 2) == round(move_curve[i],2):
                    reached = True
                    if showprogress == 'gui' or showprogress == 'console':
                        progressbar.update()
                #The machine may move beyond the desired value at this step. In this case we move on as well
                elif (round(cur_val,2) > round(move_curve[i],2)) and direction == 'up':
                     reached = True
                     if showprogress == 'gui' or showprogress == 'console':
                        progressbar.update()

                elif (round(cur_val,2) < round(move_curve[i],2)) and direction == 'down':
                     reached = True
                     if showprogress == 'gui' or showprogress == 'console':
                        progressbar.update()

                #Rounding errors around the decimal 5 are caught here by comparing only the first two decimals
                elif math.floor(100*cur_val) == math.floor(100*move_curve[i]):
                     reached = True
                     if showprogress == 'gui' or showprogress == 'console':
                        progressbar.update()

        if showprogress == 'gui' or showprogress == 'console':
            progressbar.close()


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


def sweep(device, variable, start, stop, rate, npoints, filename, plot=True, plotlist=None, sweepdev=None, md=None):
    """
    The sweep command sweeps the <variable> of <device>, from <start> to <stop>.
    Sweeping is done at <rate> and <npoints> are recorded to a datafile saved
    as <filename>.
    For measurements, the 'measurement dictionary', meas_dict, is used.
    """    
    print('Starting a sweep of "' + variable + '" from ' + str(start) + ' to ' + str(stop) + ' in ' + str(npoints) + ' steps with rate ' + str(rate) + '.')

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
    move(device, variable, start, rate)

    # Create sweep_curve
    sweep_curve = np.round(np.linspace(start, stop, npoints), 3)
    
    # Initialize plotlist if none given
    if plotlist is None:
        plotlist = list(md.keys())
    
    # Initialize plot
    if plot:
        plotsweep = []
        plotdata = list(range(len(md)))
        curve = list(range(len(md)))
        pw = list(range(len(md)))

        n = 0
        for key in plotlist:
            pw[n] = pg.PlotWidget()
            
            pw[n].showGrid(True, True)
            pw[n].setLabel('left', text=key)
            pw[n].setLabel('bottom', text=sweepdev)
            
            curve[n] = pw[n].plot()
            pw[n].show()
            pw[n].setWindowTitle(key)
            
            plotdata[n] = []
            
            n += 1
            
    # Perform sweep
    i = 0
    def update():
        nonlocal pw, curve, plotdata, i
        if i == npoints - 1:
            timer.stop()

        # Make sure we move first before measuring.
        # Has to be done this way as waiting is done at the end.
        if i != 0:
            # Measure first..
            print('   Performing measurement.')
            data = np.hstack((sweep_curve[i], measure()))
    
            if plot:
                # Plot stuff
                plotsweep.append(sweep_curve[i])
                latestData = measure()
    
                j = 0
                k = 0
                for key in md.keys():
                    if key in plotlist:
                        plotdata[k].append(latestData[j])
                        curve[k].setData(plotsweep, plotdata[k])   
                        k += 1
                    j += 1
    
            # Write stuff
            datastr = np.array2string(data, separator=', ')[1:-1].replace('\n', '')
            with open(filename, 'a') as file:
                file.write(datastr + '\n')

        if i != npoints:
            # Move to measurement value
            print('Sweeping to: {}'.format(sweep_curve[i]))
            move(device, variable, sweep_curve[i], rate, showprogress='none')
            
            # Print that we're waiting
            print('   Waiting for measurement...')

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


def record(dt, npoints, filename, plot=True, plotlist=None, md=None):
    """
    The record command records (and by default, plots) data with a time
    interval of <dt> seconds. It will record data for a number of <npoints> and
    store it in <filename>.
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
    
    # Initialize plotlist if none given
    if plotlist is None:
        plotlist = list(md.keys())
    
    # Initialize plot
    if plot:
        plottime = []
        plotdata = list(range(len(plotlist)))
        curve = list(range(len(plotlist)))
        pw = list(range(len(plotlist)))
        
        n = 0
        for key in plotlist:            
            pw[n] = pg.PlotWidget()
            
            pw[n].showGrid(True, True)
            pw[n].setLabel('left', text=key)
            pw[n].setLabel('bottom', 'time (s)')
            
            curve[n] = pw[n].plot()
            pw[n].show()
            pw[n].setWindowTitle(key)
            
            plotdata[n] = []
            
            n += 1                        

    # Perform record
    i = 0
    def update():
        nonlocal pw, curve, plotdata, i
        if i == npoints - 1:
            timer.stop()
            
        print('Performing measurement at t = ' + str(i*dt) + ' s.')

        # Plot stuff
        if plot:
            plottime.append(i*dt)
            latestData = measure()
            
            j = 0
            k = 0
            for key in md.keys():
                if key in plotlist:
                    plotdata[k].append(latestData[j])
                    curve[k].setData(plottime, plotdata[k])   
                    k += 1
                j += 1

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
    
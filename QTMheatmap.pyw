# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 23:11:25 2020
@author: Daan Wielens

/--------------------------------------\
|      Live Plotting of QTM data       |
|           Version 1.3                |
|           D.H. Wielens               |
\--------------------------------------/

This script can quickly plot (1D) sweeps generated with the QTMtoolbox.
When "Live plot" is enabled, it will automatically plot the .csv file
in the data folder which has the most recent timestamp, and it will
update the plot regularly. 

This version is for standalone use, hence the .pyw extension.

Updated to include heatmaps by K. van Dam
"""

# Step 1: Build functional GUI

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
import os
import numpy as np

# Change the working directory to the QTMtoolbox directory (where the script itself should be)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from qtmimport.qtmimport import *

# Main window
class MainWindow(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self.setWindowTitle('QTMheatmap v1.0 (2025-07-14)')
        window_icon=QIcon()
        window_icon.addFile('icons/QTMplotIcon32.png')
        self.setWindowIcon(window_icon)
        
    # --- Define layout --- 
        # Main layout: vertical structure
        layout1 = QVBoxLayout()
        layout1.setContentsMargins(8,8,8,8)
        layout1.setSpacing(10)
        
        # Top layer: "toolbar"-like bar
        layout2 = QHBoxLayout()
        self.livePlot = QCheckBox('Live plot  ')
        self.livePlot.stateChanged.connect(self.livePlotToggle)
        layout2.addWidget(self.livePlot)
        vsep = QFrame()
        vsep.setFrameShape(QFrame.VLine)
        layout2.addWidget(vsep) 
        
        filebtn = QPushButton('', self)
        filebtn.setIcon(QIcon('icons/folder-horizontal-open.png'))
        filebtn.setIconSize(QSize(16, 16))
        filebtn.clicked.connect(self.openFileNameDialog)
        layout2.addWidget(filebtn)
        layout2.addWidget(QLabel('File path:'))
        self.file_path = QLineEdit()
        layout2.addWidget(self.file_path)
        layout1.addLayout(layout2)

        # Middle section: graph
        self.graphs = QStackedLayout()
        layout1.addLayout(self.graphs)
        self.graphWidget = pg.PlotWidget()
        self.graphs.addWidget(self.graphWidget)
        self.imageWidget = pg.PlotWidget()
        self.graphs.addWidget(self.imageWidget)

        # Bottom layer: axes selectors
        layout3 = QHBoxLayout()
        layout3.addWidget(QLabel('x-axis: '))
        self.xbox = QComboBox()
        layout3.addWidget(self.xbox)
        self.xbox.activated.connect(self.xboxindex)
        vsep2 = QFrame()
        vsep2.setFrameShape(QFrame.VLine)
        layout3.addWidget(vsep2)  
        layout3.addWidget(QLabel('y-axis: '))
        self.ybox = QComboBox()
        layout3.addWidget(self.ybox)
        self.ybox.activated.connect(self.yboxindex)
        layout1.addLayout( layout3 )
        vsep3 = QFrame()
        vsep3.setFrameShape(QFrame.VLine)
        layout3.addWidget(vsep3)  
        layout3.addWidget(QLabel('Values: '))
        self.zbox = QComboBox()
        layout3.addWidget(self.zbox)
        self.zbox.activated.connect(self.zboxindex)
        self.slowbox = QCheckBox('Swap slow axis')
        layout3.addWidget(self.slowbox)
        layout1.addLayout( layout3 )
        
        # Add some shortcuts for convenience
        # self.shortcut = QShortcut(QKeySequence('Ctrl+O'), self)
        # self.shortcut.activated.connect(self.openFileNameDialog)
        # self.shortcut = QShortcut(QKeySequence('Ctrl+L'), self)
        # self.shortcut.activated.connect(self.changeLivePlot)
        # self.shortcut = QShortcut(QKeySequence('Ctrl+R'), self) # Conform Origin
        # self.shortcut.activated.connect(self.plotAutoRange)
        # self.shortcut = QShortcut(QKeySequence('Ctrl+A'), self) 
        # self.shortcut.activated.connect(self.contAutoRange)
        
        widget = QWidget()
        widget.setLayout(layout1)
        self.setCentralWidget(widget)
        
    # --- Setup plot window
        # Change background color
        self.graphWidget.setBackground('w')
        # Add top + right axes, remove their ticks
        self.graphWidget.showAxis('top', True)
        self.graphWidget.showAxis('right', True)
        self.graphWidget.getAxis('top').setTicks([])
        self.graphWidget.getAxis('right').setTicks([])
        # Add line object that can be updated later on
        self.x = []
        self.y = []
        self.pen = pg.mkPen(color=(31, 119, 180), width=1)
        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=self.pen, symbol='o', symbolSize=5, symbolBrush=(31, 119, 180), symbolPen=(31, 119, 180))
        
        # Add image item
        self.imageWidget.setBackground('w')
        self.image = pg.ImageItem(np.zeros((1,1)))
        self.imageWidget.addItem(self.image)
        self.colorbar = self.imageWidget.addColorBar(self.image, colorMap=pg.colormap.get('CET-D1'), interactive=False)
        
        # Set (x,y) indices to (0,1) for initial plot
        self.xindex = 0
        self.yindex = 1
        self.zindex = 2
        
        self.filename = ''
                
    # --- Add signals and slots
    def livePlotToggle(self, s):
        # Note: s = 2 (True) or s = 0 (False)
        if s == 2:
            self.timer = QTimer()
            self.timer.setInterval(100)
            self.timer.timeout.connect(self.livePlotting)
            self.timer.start()
        if s == 0:
            self.timer.stop()
                
    def updateData(self, xindex, yindex, zindex=-1, newFile=False):
        # Load data
        self.data = parse_data(self.filename)
        # Update comboboxes with options
        """
        ONLY update ComboBox contents when name is changed
        """
        if newFile == True:
            self.var_names = [item.name for item in self.data]
            self.xbox.clear()
            self.ybox.clear()
            self.zbox.clear()
            self.xbox.addItems(self.var_names)
            self.ybox.addItems(self.var_names)
            self.var_names.append("<none>")
            self.zbox.addItems(self.var_names)
            # Set combobox "picked item" to right value
            self.xbox.setCurrentIndex(xindex)
            self.ybox.setCurrentIndex(yindex)
            self.zindex = len(self.var_names) - 1
            self.zbox.setCurrentIndex(self.zindex)
        # If the file contains no data, clear the plot and initialize empty figure
        if len(self.data[xindex].data) == 0: 
            self.graphs.setCurrentWidget(self.graphWidget)
            self.x = []
            self.y = []
            self.graphWidget.clear()
            self.data_line = self.graphWidget.plot(self.x, self.y, pen=self.pen, symbol='o', symbolSize=5, symbolBrush=(31, 119, 180), symbolPen=(31, 119, 180))
        else:
            if zindex == -1 or zindex == len(self.var_names) - 1:
                # Show line plot
                self.graphs.setCurrentWidget(self.graphWidget)
                self.zindex = len(self.var_names) - 1
                self.zbox.setCurrentIndex(self.zindex)
                # Store data to (x,y) variables, then update the line
                self.x = self.data[xindex].data
                self.y = self.data[yindex].data
                self.data_line.setData(self.x, self.y)
            else:
                # Show image plot
                self.graphs.setCurrentWidget(self.imageWidget)
                # Store data to variables
                self.x = self.data[xindex].data
                self.y = self.data[yindex].data
                self.z = self.data[zindex].data
                # Find the sweep size and reshape the array
                if not self.slowbox.isChecked():
                    length = np.argmax(self.x != self.x[0])
                    cutoff = max(int(len(self.z) / length), 1)
                    self.z = np.reshape(self.z[:length*cutoff], (-1, length))
                    self.image.setImage(self.z)
                    self.image.setRect(QRectF(self.x[0] - 0.5 * (self.x[length] - self.x[0]), self.y[0] - 0.5 * (self.y[1] - self.y[0]), self.x[-1] - self.x[0] + (self.x[length] - self.x[0]), self.y[length-1] - self.y[0] + (self.y[1] - self.y[0])))
                else:
                    length = np.argmax(self.y != self.y[0])
                    cutoff = max(int(len(self.z) / length), 1)
                    self.z = np.reshape(self.z[:length*cutoff], (-1, length)).T
                    self.image.setImage(self.z)
                    self.image.setRect(QRectF(self.x[0] - 0.5 * (self.x[1] - self.x[0]), self.y[0] - 0.5 * (self.y[length] - self.y[0]), self.x[length-1] - self.x[0] + (self.x[1] - self.x[0]), self.y[-1] - self.y[0] + (self.y[length] - self.y[0])))
                self.colorbar.setLevels(low = np.min(self.z), high = np.max(self.z))
        # Update axes labels
        self.graphWidget.setLabel('bottom', self.var_names[xindex], color='black', size=15)
        self.graphWidget.setLabel('left', self.var_names[yindex], color='black', size=15)
        self.imageWidget.setLabel('bottom', self.var_names[xindex], color='black', size=15)
        self.imageWidget.setLabel('left', self.var_names[yindex], color='black', size=15)
    
    def xboxindex(self, i):
        self.xindex = i
        self.updateData(self.xindex, self.yindex)
        self.graphWidget.autoRange()
    
    def yboxindex(self, i):
        self.yindex = i
        self.updateData(self.xindex, self.yindex)
        self.graphWidget.autoRange()
    
    def zboxindex(self, i):
        self.zindex = i
        if self.zindex == len(self.var_names) - 1:
            self.updateData(self.xindex, self.yindex)
        else:
            self.updateData(self.xindex, self.yindex, self.zindex)
        
    def plotAutoRange(self):
        self.graphWidget.autoRange()
        
    def contAutoRange(self):
        self.graphWidget.enableAutoRange()
        
    def livePlotting(self):
        # We monitor the folder given here:
        folder = 'Data'
        stamps = []
        # Get recursive list of files:
        files = [os.path.join(dp, f) for dp, dn, fn in os.walk('Data') for f in fn]
        for file in files:
            stamps.append(os.path.getmtime(file))
        #if len(files) == 0:
        #    return
        # Find which files are .csv
        max_stamp = 0
        latest_file = ''
        for f, s in zip(files, stamps):
            if '.csv' in f:
                if s > max_stamp:
                    max_stamp = s
                    latest_file = f
        # Proceed to plot
        if len(latest_file) > 0:
            if os.path.abspath(latest_file) == self.filename:
                self.updateData(self.xindex, self.yindex, self.zindex)
            else:
                self.filename = os.path.abspath(latest_file)
                self.updateData(self.xindex, self.yindex, newFile=True)
            self.file_path.setText(self.filename)
            
    def changeLivePlot(self):
        if self.livePlot.isChecked():
            self.livePlot.setChecked(False)
        else:
            self.livePlot.setChecked(True)
        
        
    def openFileNameDialog(self):
        # Since we open a file, we stop live plotting
        self.livePlot.setChecked(False)
        options = QFileDialog.Options()
        # Let's use the Native dialog as it is easier for the user
        #options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"Open a measurement file", "","Text files (*.csv);;All files (*)", options=options)
        if fileName:
            self.filename = fileName
            self.updateData(self.xindex, self.yindex, newFile=True)
            self.file_path.setText(self.filename)       

# Run main code
app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
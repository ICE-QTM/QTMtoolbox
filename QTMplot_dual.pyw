# -*- coding: utf-8 -*-
"""
/--------------------------------------\
|      Live Plotting of QTM data       |
|           Version 1.0                |
|           D.H. Wielens               |
\--------------------------------------/
The 'dual' version can plot two lines simultaneously.
"""

# Step 1: Build functional GUI
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from functions.qtmimport import *
import os

# Change the working directory to the QTMtoolbox directory (where the script itself should be)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Main window
class MainWindow(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self.setWindowTitle('QTMplot - dual version v1.0 (2025-05-02)')
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
        self.graphWidget = pg.PlotWidget()
        layout1.addWidget(self.graphWidget)

        # Bottom layer: axes selectors
        layout3 = QHBoxLayout()
        layout3.addWidget(QLabel('x-axis: '))
        self.xbox = QComboBox()
        layout3.addWidget(self.xbox)
        self.xbox.activated.connect(self.xboxindex)
        vsep2 = QFrame()
        vsep2.setFrameShape(QFrame.VLine)
        layout3.addWidget(vsep2)  
        layout3.addWidget(QLabel('y-axis 1: '))
        self.ybox = QComboBox()
        layout3.addWidget(self.ybox)
        self.ybox.activated.connect(self.yboxindex)
        layout1.addLayout( layout3 )
        
        # Bottom layer 2: second y-axis selector
        layout4 = QHBoxLayout()
        layout4.addWidget(QLabel('y-axis 2: '))
        self.ybox2 = QComboBox()
        layout4.addWidget(self.ybox2)
        self.ybox2.activated.connect(self.ybox2index)
        layout1.addLayout(layout4)
        
        # Add some shortcuts for convenience
        self.shortcut = QShortcut(QKeySequence('Ctrl+O'), self)
        self.shortcut.activated.connect(self.openFileNameDialog)
        self.shortcut = QShortcut(QKeySequence('Ctrl+L'), self)
        self.shortcut.activated.connect(self.changeLivePlot)
        self.shortcut = QShortcut(QKeySequence('Ctrl+R'), self) # Conform Origin
        self.shortcut.activated.connect(self.plotAutoRange)
        self.shortcut = QShortcut(QKeySequence('Ctrl+A'), self) 
        self.shortcut.activated.connect(self.contAutoRange)
        
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
        self.y2 = []
        self.pen = pg.mkPen(color=(31, 119, 180), width=1)
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=self.pen, symbol='o', symbolSize=5, symbolBrush=(31, 119, 180), symbolPen=(31, 119, 180))
        self.data_line2 = self.graphWidget.plot(self.x, self.y2, pen=self.pen, symbol='o', symbolSize=5, symbolBrush=(242, 142, 43), symbolPen=(242, 142, 43))
        
        
        # Set (x,y) indices to (0,1) for initial plot
        self.xindex = 0
        self.yindex = 1
        self.yindex2 = 2
        
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
                
    def updateData(self, xindex, yindex, yindex2, newFile=False):
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
            self.ybox2.clear()
            self.xbox.addItems(self.var_names)
            self.ybox.addItems(self.var_names)
            self.ybox2.addItems(self.var_names)
            # Set combobox "picked item" to right value
            self.xbox.setCurrentIndex(xindex)
            self.ybox.setCurrentIndex(yindex)
            self.ybox2.setCurrentIndex(yindex2)
        # If the file contains no data, clear the plot and initialize empty figure
        if len(self.data[xindex].data) == 0: 
            self.x = []
            self.y = []
            self.y2 = []
            self.graphWidget.clear()
            self.data_line = self.graphWidget.plot(self.x, self.y, pen=self.pen, symbol='o', symbolSize=5, symbolBrush=(31, 119, 180), symbolPen=(31, 119, 180))
            self.data_line2 = self.graphWidget.plot(self.x, self.y2, pen=self.pen, symbol='o', symbolSize=5, symbolBrush=(242, 142, 43), symbolPen=(242, 142, 43))
        else:
            # Store data to (x,y) variables, then update the line
            self.x = self.data[xindex].data
            self.y = self.data[yindex].data
            self.y2 = self.data[yindex2].data
            self.data_line.setData(self.x, self.y)
            self.data_line2.setData(self.x, self.y2)
        # Update axes labels
        self.graphWidget.setLabel('bottom', self.var_names[xindex], color='black', size=15)
        self.graphWidget.setLabel('left', '1: ' + self.var_names[yindex] + ', 2: ' + self.var_names[yindex2], color='black', size=15)
    
    def xboxindex(self, i):
        self.xindex = i
        self.updateData(self.xindex, self.yindex, self.yindex2)
        self.graphWidget.autoRange()
    
    def yboxindex(self, i):
        self.yindex = i
        self.updateData(self.xindex, self.yindex, self.yindex2)
        self.graphWidget.autoRange()
        
    def ybox2index(self, i):
        self.yindex2 = i
        self.updateData(self.xindex, self.yindex, self.yindex2)
        self.graphWidget.autoRange()
        
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
                self.updateData(self.xindex, self.yindex, self.yindex2)
            else:
                self.filename = os.path.abspath(latest_file)
                self.updateData(self.xindex, self.yindex, self.yindex2, newFile=True)
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
            self.updateData(self.xindex, self.yindex, self.yindex2, newFile=True)
            self.file_path.setText(self.filename)       

# Run main code
app = QApplication([])
window = MainWindow()
window.show()
app.exec_()

#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# pumpControl: A wrapper class for the a generic pump
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 2/15/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import serial
import sys
import time
from PyQt4 import QtCore, QtGui
from rainin_rp1 import RaininRP1

# ----------------------------------------------------------------------------------------
# PumpControl Class Definition
# ----------------------------------------------------------------------------------------
class PumpControl(QtGui.QWidget):
    def __init__(self,
                 parent = None,
                 COM_port = 3,
                 pump_ID = 30,
                 simulate = False,
                 verbose = True):

        #Initialize parent class
        QtGui.Qidget.__init__(self, parent)

        # Define internal attributes
        self.COM_port = COM_port
        self.pump_ID = pump_ID
        self.simulate = simulate
        self.verbose = verbose
        self.status_repeat_time = 2000
        
        # Create Instance of Pump
        self.pump = RaininRP1(COM_port = self.COM_port,
                              pump_ID = self.pump_ID,
                              simulate = self.simulate,
                              verbose = self.verbose)

        # Create GUI Elements
        self.createGUI()

        # Define timer for periodic polling of pump status
        self.status_timer = QtCore.QTimer()        
        self.status_timer.setInterval(self.status_repeat_time)
        self.status_timer.timeout.connect(self.pollPumpStatus)
        self.status_timer.start()

    # ------------------------------------------------------------------------------------
    # Close class
    # ------------------------------------------------------------------------------------
    def close(self):
        if self.verbose: "Print closing pump"
        self.pump.close()

    # ----------------------------------------------------------------------------------------
    # Display Status
    # ----------------------------------------------------------------------------------------
    def getStatus(self):
        return
    
    # ----------------------------------------------------------------------------------------
    # Poll Pump Status
    # ----------------------------------------------------------------------------------------
    def pollPumpStatus(self):
        self.displayStatus(self.pump.getStatus())

    

    
    # ----------------------------------------------------------------------------------------
    # setPumpConfiguration
    # ----------------------------------------------------------------------------------------
    # Populate the configratuion display

    # ----------------------------------------------------------------------------------------
    # setPumpDirection
    # ----------------------------------------------------------------------------------------
    # Set the pump direction widget

    # ----------------------------------------------------------------------------------------
    # setStatus
    # ----------------------------------------------------------------------------------------
    # Set the pump status display

    

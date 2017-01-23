#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A wrapper class for the custom valve widget defined in ui_layouts/ui_qt_valve.
# This class provides the basic I/O required to set and read various valve
# properties. 
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/28/13
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import storm_control.fluidics.valves.ui_layouts.ui_qt_valve as uiQtValve

# ----------------------------------------------------------------------------------------
# QtValveControl Class Definition
# ----------------------------------------------------------------------------------------
class QtValveControl(QtWidgets.QWidget):

    # Define custom signals
    change_port_signal = QtCore.pyqtSignal(int)
    
    def __init__(self,
                 parent = None,
                 ID = 0,
                 valve_name = "Valve 0",
                 configuration = "Default",
                 port_names = ("Port 1", "Port 2"),
                 desired_port = 0,
                 rotation_directions = ("Clockwise", "Counter Clockwise"),
                 desired_rotation = 0,
                 status = ("Undefined", False),
                 error = ("None", False),
                 verbose = True,
                 ):

        # Initialize parent
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = uiQtValve.Ui_QtValveControlWidget()
        self.ui.setupUi(self)
        
        # Set internal variables
        self.valve_ID = ID
        self.max_ports = len(port_names)
        self.max_rotation = len(rotation_directions)
        self.verbose = verbose
        
        # Configure display objects
        self.setValveName(valve_name)
        self.setValveConfiguration(configuration)
        self.setPortNames(port_names)
        self.setCurrentDesiredPort(desired_port)
        self.setRotationDirections(rotation_directions)
        self.setCurrentDesiredRotation(desired_rotation)
        self.setStatus(status)
        self.setError(error)

        # Connect signal to change port button
        self.ui.changePortButton.clicked.connect(self.changePortSignal)

    # ------------------------------------------------------------------------------------
    # Emit custom signal when a change port command is issued
    # ------------------------------------------------------------------------------------  
    def changePortSignal(self):
        self.change_port_signal.emit(self.valve_ID)

    # ------------------------------------------------------------------------------------
    # Return selected rotation index
    # ------------------------------------------------------------------------------------  
    def getDesiredRotationIndex(self):
        return self.ui.desiredRotationComboBox.currentIndex()

    # ------------------------------------------------------------------------------------
    # Return current valve error: Reserved for future use
    # ------------------------------------------------------------------------------------  
    def getError(self, error):
        pass  

    # ------------------------------------------------------------------------------------
    # Set the current port ID
    # ------------------------------------------------------------------------------------  
    def getPortIndex(self):
        return self.ui.desiredPortComboBox.currentIndex()

    # ------------------------------------------------------------------------------------
    # Return displayed valve configuration
    # ------------------------------------------------------------------------------------  
    def getValveConfiguration(self):
        return self.ui.valveConfigurationLabel.text()

    # ------------------------------------------------------------------------------------
    # Return displayed valve name
    # ------------------------------------------------------------------------------------  
    def getValveName(self):
        return self.ui.valveGroupBox.title()

    # ------------------------------------------------------------------------------------
    # Set the desired port
    # ------------------------------------------------------------------------------------  
    def setCurrentDesiredPort(self, desired_port):
        if (desired_port > (self.max_ports -1 )):
            desired_port = 0
        self.ui.desiredPortComboBox.setCurrentIndex(desired_port)

    # ------------------------------------------------------------------------------------
    # Set current rotation direction
    # ------------------------------------------------------------------------------------  
    def setCurrentDesiredRotation(self, desired_rotation):
        if (desired_rotation > (self.max_rotation -1 )):
            desired_rotation = 0
        self.ui.desiredRotationComboBox.setCurrentIndex(desired_rotation) 

    # ------------------------------------------------------------------------------------
    # Set enabled status for display items
    # ------------------------------------------------------------------------------------          
    def setEnabled(self, is_enabled):
        self.ui.desiredPortComboBox.setEnabled(is_enabled)
        self.ui.changePortButton.setEnabled(is_enabled)
        self.ui.desiredRotationComboBox.setEnabled(is_enabled)

    # ------------------------------------------------------------------------------------
    # Set current valve error: Reserved for future use
    # ------------------------------------------------------------------------------------  
    def setError(self, error):
        pass

    # ------------------------------------------------------------------------------------
    # Set port names for display
    # ------------------------------------------------------------------------------------  
    def setPortNames(self, port_names):
        self.ui.desiredPortComboBox.clear()
        for name in port_names:
            self.ui.desiredPortComboBox.addItem(name)

    # ------------------------------------------------------------------------------------
    # Set possible rotation directions
    # ------------------------------------------------------------------------------------  
    def setRotationDirections(self, rotation_directions):
        self.ui.desiredRotationComboBox.clear()
        for name in rotation_directions:
            self.ui.desiredRotationComboBox.addItem(name)

    # ------------------------------------------------------------------------------------
    # Set current valve status
    # ------------------------------------------------------------------------------------  
    def setStatus(self, status):
        # Set Label Text
        self.ui.valveStatusLabel.setText(status[0])
        if status[1] == True:
            self.ui.valveStatusLabel.setStyleSheet("QLabel { color: red}")
        if status[1] == False:
            self.ui.valveStatusLabel.setStyleSheet("QLabel { color: black}")     

    # ------------------------------------------------------------------------------------
    # Set valve configuration for display
    # ------------------------------------------------------------------------------------  
    def setValveConfiguration(self, configuration):
        self.ui.valveConfigurationLabel.setText(configuration)

    # ------------------------------------------------------------------------------------
    # Set valve name for display
    # ------------------------------------------------------------------------------------  
    def setValveName(self, name):
        self.ui.valveGroupBox.setTitle(name)

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # Scroll area widget contents - layout
        self.scrollLayout = QtGui.QVBoxLayout()

        # Scroll area widget contents
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.scrollLayout)

        # Scroll area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # Main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # Add all main to the main vLayout
        self.mainLayout.addWidget(self.scrollArea)

        self.valve_widgets = []
        for ID in range(3):
            wid = QtValveControl(self, ID = ID, valve_name = "Valve " + str(ID))
            wid.change_port_signal.connect(self.detectEmittedSignal)
            self.valve_widgets.append(wid)
            self.scrollLayout.addWidget(self.valve_widgets[-1])

        self.scrollLayout.addStretch(1)
        
        # Central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # Set central widget
        self.setCentralWidget(self.centralWidget)
        
    # ------------------------------------------------------------------------------------
    # Detect custom signal
    # ------------------------------------------------------------------------------------    
    def detectEmittedSignal(self, valve_ID):
        print("Detected signal from valve index: " + str(valve_ID))
        print("Found port index: " + str(self.valve_widgets[valve_ID].getPortIndex()))

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------
if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#



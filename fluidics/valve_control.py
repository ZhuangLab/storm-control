#
# Class the controls the interface with the hamilton valves
#
# Jeff Moffitt
# jeffmoffitt@gmail.com
# December 20, 2013
#

import os
import sys
from PyQt4 import QtCore, QtGui
import qt_valve_control
import hamilton

class ValveControls(QtGui.QWidget):
    valve_button_push = QtCore.pyqtSignal(int)

    ## __init__
    #
    # @param parent (Optional) the PyQt parent of this object.
    #
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        # Initialize hamilton class
        self.hamilton = hamilton.HamiltonMVP(verbose = False)

        self.pollValveStatus()
        
        # Define timer for periodic polling of valve status
        self.valve_poll_timer = QtCore.QTimer()        
        self.valve_poll_timer.setInterval(1000)
        self.valve_poll_timer.timeout.connect(self.PollValveStatus)
        self.valve_poll_timer.start()

        # Create GUI properties
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.qtValveWidgets = []

        # Add valves
        numFoundValves = self.hamilton.howManyValves()
        if numFoundValves == 0:
            print "No valves found!"
        else:
            for i in range(numFoundValves):
                newWidget = QValveControl(i, self.hamilton.whatIsValveConfiguration())
                newWidget.moveValveButtonSignal.connect(self.retransmit)
                self.qtValveWidgets.append(newWidget)
            
            self.layout.addWidget(newWidget)
            print "Added valve control"
     
    def retransmit(self, valve_ID):
        self.moveValveButtonSignal2.emit(valve_ID)

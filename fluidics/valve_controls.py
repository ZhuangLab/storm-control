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

        # Display Loading Graphic
        
        # Initialize Hamilton Class
        self.hamilton = hamilton.HamiltonMVP(verbose = False)

        # Define timer for periodic polling of valve status
        self.valve_poll_timer = QtCore.QTimer()        
        self.valve_poll_timer.setInterval(1000)
        #self.valve_poll_timer.timeout.connect(self.pollValveStatus)
        self.valve_poll_timer.start()
        
        # Create GUI properties
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.qtValveWidgets = []
        
        # Add valves
        num_found_valves = self.hamilton.howManyValves()
        if num_found_valves == 0:
            print "No valves found!"
        else:
            for valve_ID in range(num_found_valves):
                newWidget = qt_valve_control.QValveControl(valve_ID,
                                                           self.hamilton.whatIsValveConfiguration(valve_ID))
                newWidget.moveValveButtonSignal.connect(self.retransmit)
                self.qtValveWidgets.append(newWidget)
            
            self.layout.addWidget(newWidget)
            print "Added valve control"
         
    def retransmit(self, valve_ID):
        self.moveValveButtonSignal2.emit(valve_ID)

## Test Code
class Main(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(Main, self).__init__(parent)

        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # Create Valve Widget
        self.valveControlWidget = ValveControls()
        self.mainLayout.addWidget(self.valveControlWidget)

        # Define Central Widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)
                
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myWidget = Main()
    myWidget.show()
    app.exec_()

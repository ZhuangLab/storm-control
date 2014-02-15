#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A wrapper class for a chain of pumps. 
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 2/15/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
from PyQt4 import QtCore, QtGui
from qtPumpControl import QtPumpControl
from rainin_rp1 import RaininRP1

# ----------------------------------------------------------------------------------------
# PumpChain Class Definition
# ----------------------------------------------------------------------------------------
class PumpChain(QtGui.QWidget):
    def __init__(self,
                 parent = None,
                 com_port = 2,
                 num_simulated_pumps = 0,
                 verbose = False
                 ):

        # Initialize parent class
        QtGui.QWidget.__init__(self, parent)

        # Define local attributes
        self.COM_port = com_port
        self.verbose = verbose
        self.poll_time = 2000

        # Create instance of Rainin class
        if num_simulated_valves > 0:
            self.pump_chain = RaininRP1(COM_port = 0,
                                         num_simulated_pumps = num_simulated_pumps,
                                         verbose = self.verbose)
        else:
            self.pump_chain = RaininRP1(COM_port = self.COM_port,
                                         verbose = self.verbose)

        # Create QtValveControl widgets for each valve in the chain
        self.num_pumps = self.pump_chain.howManyPumps()
        self.pump_names = []
        self.pump_widgets = []
        
        # Create GUI
        self.createGUI() # Widgets created here

        # Define timer for periodic polling of valve status
        self.pump_poll_timer = QtCore.QTimer()        
        self.pump_poll_timer.setInterval(self.poll_time)
        self.pump_poll_timer.timeout.connect(self.pollValveStatus)
        self.pump_poll_timer.start()

    # ------------------------------------------------------------------------------------
    # Close class
    # ------------------------------------------------------------------------------------
    def close(self):
        if self.verbose: "Print closing pump chain"
        self.pump_chain.close()

    # ------------------------------------------------------------------------------------
    # Create the Qt widgets for display
    # ------------------------------------------------------------------------------------  
    def createGUI(self):
        # Define display widget
        self.pumpChainGroupBox = QtGui.QGroupBox()
        self.pumpChainGroupBox.setTitle("Valve Controls")
        self.pumpChainGroupBoxLayout = QtGui.QVBoxLayout(self.pumpChainGroupBox)

        for pump_ID in range(self.num_pumps):
            pump_widget = QtPumpControl(self,
                                        ID = pump_ID)
            self.pump_names.append(str(pump_ID + 1)) # Save pump name
            pump_widget.setPumpName("Pump " + str(pump_ID+1)) # Valve names are +1 valve IDs
            pump_widget.setPumpConfiguration(self.pump_chain.howIsValveConfigured(pump_ID))
            pump_widget.setPumpDirection(self.pump_chain.getDirections(pump_ID))
            pump_widget.setStatus(self.pump_chain.getStatus(pump_ID))

            pump_widget.change_pump_signal.connect(self.changeValvePosition)

            self.pump_widgets.append(pump_widget)

            self.pumpChainGroupBoxLayout.addWidget(pump_widget)

        self.pumpChainGroupBoxLayout.addStretch(1)

        # Define main widget
        self.mainWidget = self.pumpChainGroupBox

        # Define menu items
        self.pump_reset_action = QtGui.QAction("Pump Chain Reset", self)
        self.pump_reset_action.triggered.connect(self.reinitializeChain)

        self.menu_names = ["Pumps"]
        self.menu_items = [[self.pump_reset_action]]

    # ------------------------------------------------------------------------------------
    # Determine number of pumps
    # ------------------------------------------------------------------------------------
    def howManyPumps(self):
        return self.pump_chain.howManyPumps

    # ------------------------------------------------------------------------------------
    # Determine and update status of pumps
    # ------------------------------------------------------------------------------------
    def pollStatus(self):
        for pump_ID in range(self.num_pumps):
            self.pump_widgets[pump_ID].setStatus(self.pump_chain.getStatus(pump_ID))

    # ------------------------------------------------------------------------------------
    # Change pump based on external command
    # ------------------------------------------------------------------------------------          
    def receiveCommand(self, command):
##        for pump_ID, port_ID in enumerate(command):
##            if port_ID >= 0: # -1 is a flag for 'do not change port'
##                self.changeValvePosition(pump_ID, port_ID)

    # ------------------------------------------------------------------------------------
    # Reinitialize the valve chain
    # ------------------------------------------------------------------------------------          
    def reinitializeChain(self):
        self.pump_chain.resetChain()

    # ------------------------------------------------------------------------------------
    # Set enabled status for display items
    # ------------------------------------------------------------------------------------          
    def setEnabled(self, is_enabled):
        for pump_ID in range(self.num_pumps):
            self.pump_widgets[pump_ID].setEnabled(is_enabled)
    
# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.pump_chain = PumpChain(COM_port = 2,
                                    verbose = True,
                                    num_simulated_pumps = 2)
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.mainLayout.addWidget(self.pump_chain.mainWidget)
        
        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Pump Chain Control")

        # set window geometry
        self.setGeometry(50, 50, 500, 100 + 100*self.pump_chain.num_pumps)

        # Create file menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.closeEvent)

        file_menu.addAction(exit_action)

    # ------------------------------------------------------------------------------------
    # Detect close event
    # ------------------------------------------------------------------------------------    
    def closeEvent(self, event):
        self.pump_chain.close()
        self.close()

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
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


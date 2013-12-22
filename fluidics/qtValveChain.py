#!/usr/bin/python
import sys
from PyQt4 import QtCore, QtGui
from qtValveControl import QtValveControl
from hamilton import HamiltonMVP

class QtValveChain(QtGui.QWidget):
    def __init__(self,
                 parent = None,
                 COM_port = 2,
                 verbose = True,
                 num_simulated_valves = 0,
                 ):

        ## Is this necessary?
        QtGui.QWidget.__init__(self, parent)

        # Define local attributes
        self.COM_port = COM_port
        self.verbose = verbose

        # Define display widget
        self.scrollLayout = QtGui.QVBoxLayout()
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.scrollLayout)
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # Create Valve Chain
        if num_simulated_valves > 0:
            self.valve_chain = HamiltonMVP(COM_port = 0,
                                           simulate = True,
                                           num_simulated_valves = num_simulated_valves)
        else:
            self.valve_chain = HamiltonMVP(COM_port = self.COM_port,
                                           verbose = self.verbose)
            
        # Create Valve Controls for Each Valve in the Chain
        self.num_valves = self.valve_chain.howManyValves()

        self.valve_widgets = []
        for valve_ID in range(self.num_valves):
            valve_widget = QtValveControl(self,
                                         ID = valve_ID)
            valve_widget.setValveName("Valve " + str(valve_ID))
            valve_widget.setValveConfiguration(self.valve_chain.howIsValveConfigured(valve_ID)[0])
            valve_widget.setPortNames(self.valve_chain.getDefaultPortNames(valve_ID))
            valve_widget.setRotationDirections(self.valve_chain.getRotationDirections(valve_ID))
            valve_widget.setStatus(self.valve_chain.getStatus(valve_ID))

            valve_widget.changePortButton.clicked.connect(self.changeValvePosition)

            self.valve_widgets.append(valve_widget)

            self.scrollLayout.addWidget(valve_widget)

        self.scrollLayout.addStretch(1)
        
        # Define timer for periodic polling of valve status
        self.valve_poll_timer = QtCore.QTimer()        
        self.valve_poll_timer.setInterval(1000)
        self.valve_poll_timer.timeout.connect(self.pollValveStatus)

    def changeValvePosition(self, valve_ID):
        pass

    def pollValveStatus(self):
        for valve_ID in range(self.num_valves):
            self.valve_widgets[valve_ID].setStatus(self.valve_chain.getStatus(valve_ID))
                       
### Stand alone code
class Window(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(Window, self).__init__(parent)

        # scroll area widget contents - layout
        self.valve_chain_widget = QtValveChain(COM_port = 2,
                                               verbose = True,
                                               num_simulated_valves = 3)
        
        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.valve_chain_widget.scrollArea)
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()                              

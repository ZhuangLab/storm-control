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
        self.scrollArea.setWdigetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)
        
        # Create Valve Chain
        self.valve_chain = HamiltonMVP(COM_port = self.COM_port,
                                       verbose = self.verbose)
        
        # Create Valve Controls for Each Valve in the Chain
        self.num_valves = self.valve_chain.howManyValves()

        self.valve_widgets = []
        for valve_ID in range(self.num_valves):
            valve_widget = QtValveControl(self,
                                         ID = valve_ID)
            valve_widget.setValveName("Valve " + str(ID))
            valve_widget.setValveConfiguration(self.valve_chain.howIsValveConfigured(valve_ID))
            valve_widget.setPortNames(self.valve_chain.getDefaultPortNames)
            valve_widget.setRotationDirections(self.valve_chain.getRotationDirections(valve_ID))
            valve_widget.setStatus(self.valve_chain.getStatus(valve_ID))

            valve_widget.changePortButton.clicked.connect(self.changeValvePosition)
            
        # Define timer for periodic polling of valve status
        self.valve_poll_timer = QtCore.QTimer()        
        self.valve_poll_timer.setInterval(1000)
        self.valve_poll_timer.timeout.connect(self.pollValveStatus)

    def changeValvePosition(self, valve_ID):
        pass

    def pollValveStatus(self):
        pass
                       
### Stand alone code
class Window(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(Window, self).__init__(parent)

        # scroll area widget contents - layout
        self.scrollLayout = QtGui.QVBoxLayout()

        # scroll area widget contents
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.scrollLayout)

        # scroll area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.scrollArea)

        self.valve_widgets = []
        for ID in range(3):
            wid = QtValveControl(self, ID = ID, valve_name = "Valve " + str(ID))
            wid.change_port_signal.connect(self.detectEmittedSignal)
            self.valve_widgets.append(wid)
            self.scrollLayout.addWidget(self.valve_widgets[-1])

        self.scrollLayout.addStretch(1)
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

    def detectEmittedSignal(self, valve_ID):
        print "Detected signal from valve index: " + str(valve_ID)
        print "Found port index: " + str(self.valve_widgets[valve_ID].getPortIndex())

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()                              

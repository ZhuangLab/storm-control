#!/usr/bin/python
import sys
from PyQt4 import QtCore, QtGui
from qtValveControl import QtValveControl
from hamilton import HamiltonMVP

class ValveChain(QtGui.QWidget):
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

        # Create Valve Chain
        if num_simulated_valves > 0:
            self.valve_chain = HamiltonMVP(COM_port = 0,
                                           simulate = True,
                                           num_simulated_valves = num_simulated_valves,
                                           verbose = self.verbose)
        else:
            self.valve_chain = HamiltonMVP(COM_port = self.COM_port,
                                           verbose = self.verbose)

        # Create Valve Controls for Each Valve in the Chain
        self.num_valves = self.valve_chain.howManyValves()
        self.valve_names = []
        self.valve_widgets = []

        # Create GUI
        self.createGUI()

        # Define timer for periodic polling of valve status
        self.valve_poll_timer = QtCore.QTimer()        
        self.valve_poll_timer.setInterval(1000)
        self.valve_poll_timer.timeout.connect(self.pollValveStatus)

        self.valve_poll_timer.start()

    def createGUI(self):
        # Define display widget
        self.valveChainGroupBox = QtGui.QGroupBox()
        self.valveChainGroupBox.setTitle("Valve Controls")
        self.valveChainGroupBoxLayout = QtGui.QVBoxLayout(self.valveChainGroupBox)

        for valve_ID in range(self.num_valves):
            valve_widget = QtValveControl(self,
                                         ID = valve_ID)
            self.valve_names.append(str(valve_ID + 1)) # Save valve name
            valve_widget.setValveName("Valve " + str(valve_ID+1)) # Valve names are +1 valve IDs
            valve_widget.setValveConfiguration(self.valve_chain.howIsValveConfigured(valve_ID)[0])
            valve_widget.setPortNames(self.valve_chain.getDefaultPortNames(valve_ID))
            valve_widget.setRotationDirections(self.valve_chain.getRotationDirections(valve_ID))
            valve_widget.setStatus(self.valve_chain.getStatus(valve_ID))

            valve_widget.change_port_signal.connect(self.changeValvePosition)

            self.valve_widgets.append(valve_widget)

            self.valveChainGroupBoxLayout.addWidget(valve_widget)

        self.valveChainGroupBoxLayout.addStretch(1)

        # add all main to the main vLayout
        self.mainLayout = QtGui.QVBoxLayout()
        self.mainLayout.addWidget(self.valveChainGroupBox)

        self.mainWidget = QtGui.QGroupBox()
        self.mainWidget.setLayout(self.mainLayout)
        
    def receiveCommand(self, command):
        for valve_ID, port_ID in enumerate(command):
            print valve_ID, port_ID
            if port_ID >= 0:
                self.changeValvePosition(valve_ID, port_ID)
            else:
                print "Skipped Valve " + str(valve_ID + 1)
        
    def changeValvePosition(self, valve_ID, port_ID = None):
        if port_ID == None:
            port_ID = self.valve_widgets[valve_ID].getPortIndex()
        rotation_direction = self.valve_widgets[valve_ID].getDesiredRotationIndex()

        if self.verbose:
            text_string = "Changing Valve " + str(valve_ID)
            text_string += " Port " + str(port_ID)
            text_string += " Direction " + str(rotation_direction)
            print text_string 
        
        self.valve_chain.changePort(valve_ID = valve_ID,
                                    port_ID = port_ID,
                                    direction = rotation_direction)
        self.pollValveStatus()

    def pollValveStatus(self):
        for valve_ID in range(self.num_valves):
            self.valve_widgets[valve_ID].setStatus(self.valve_chain.getStatus(valve_ID))

    def howManyValves(self):
        return self.valve_chain.howManyValves

    def close(self):
        self.valve_chain.close()
        self.valve_poll_timer.stop()
                       
### Stand alone code
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.valve_chain_widget = ValveChain(COM_port = 2,
                                               verbose = True,
                                               num_simulated_valves = 2)
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.valve_chain_widget.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Valve Chain Control")

        # set window geometry
        self.setGeometry(50, 50, 500, 100 + 100*self.valve_chain_widget.num_valves)

        # Create file menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.closeEvent)

        file_menu.addAction(exit_action)

    def closeEvent(self, event):
        self.valve_chain_widget.close()
        self.close()
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    app.exec_()                              

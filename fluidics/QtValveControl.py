#!/usr/bin/python
import sys
from PyQt4 import QtCore, QtGui
from ui_layouts.ui_qt_valve import QtValveControlWidget

class QtValveControl(QtValveControlWidget):

    # signals
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
        
        QtValveControlWidget.__init__(self, parent)
        
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
        self.changePortButton.clicked.connect(self.changePortSignal)

    def setValveName(self, name):
        self.valveGroupBox.setTitle(name)

    def getValveName(self):
        return self.valveGroupBox.title()

    def setValveConfiguration(self, configuration):
        self.valveConfigurationLabel.setText(configuration)

    def getValveConfiguration(self):
        return self.valveConfigurationLabel.text()
    
    def setPortNames(self, port_names):
        self.desiredPortComboBox.clear()

        for name in port_names:
            self.desiredPortComboBox.addItem(name)

    def setCurrentDesiredPort(self, desired_port):
        if (desired_port > (self.max_ports -1 )):
            desired_port = 0
        self.desiredPortComboBox.setCurrentIndex(desired_port)

    def getPortIndex(self):
        return self.desiredPortComboBox.currentIndex()

    def setRotationDirections(self, rotation_directions):
        self.desiredRotationComboBox.clear()
        for name in rotation_directions:
            self.desiredRotationComboBox.addItem(name)

    def setCurrentDesiredRotation(self, desired_rotation):
        if (desired_rotation > (self.max_rotation -1 )):
            desired_rotation = 0
        self.desiredRotationComboBox.setCurrentIndex(desired_rotation) 

    def getDesiredRotationIndex(self):
        return self.desiredRotationComboBox.currentIndex()

    def setStatus(self, status):
        # Set Label Text
        self.valveStatusLabel.setText(status[0])

        if status[1] == True:
            self.valveStatusLabel.setStyleSheet("QLabel { color: red}")
        if status[1] == False:
            self.valveStatusLabel.setStyleSheet("QLabel { color: black}")                

    def setError(self, error):
        pass

    def changePortSignal(self):
        if self.verbose:
            print ("Emitting signal from " + self.getValveName() +
                   ": Desired port index " + str(self.getPortIndex()) +
                   " and direction index " + str(self.getDesiredRotationIndex())
                   )
        self.change_port_signal.emit(self.valve_ID)
                       
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

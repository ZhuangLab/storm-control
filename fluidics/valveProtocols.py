#!/usr/bin/python
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt4 import QtCore, QtGui
from valveCommands import ValveCommands

class ValveProtocols(QtGui.QMainWindow):

    command_ready_signal = QtCore.pyqtSignal()
    
    def __init__(self,
                 protocol_xml_path = "default_config.xml",
                 command_xml_path = "default_config.xml",
                 verbose = False):
        super(ValveProtocols, self).__init__()

        # Initialize internal attributes
        self.verbose = verbose
        self.protocol_xml_path = protocol_xml_path
        self.command_xml_path = command_xml_path
        self.protocol_names = []
        self.protocol_commands = []
        self.protocol_durations = []
        self.num_protocols = 0
        self.status = [-1, -1] # Protocol ID, command ID within protocol
        self.issued_command = []
        
        # Create Valve Commands
        self.valveCommands = ValveCommands(xml_file_path = self.command_xml_path,
                                           verbose = self.verbose)

        # Connect valve command issue signal
        self.valveCommands.change_command_signal.connect(self.issueCommand)
        
        # Create GUI
        self.createGUI()

        # Load Configurations
        self.loadProtocols(xml_file_path = self.protocol_xml_path)

        # Create timer
        self.protocol_timer = QtCore.QTimer()
        self.protocol_timer.setSingleShot(True)
        self.protocol_timer.timeout.connect(self.advanceProtocol)

        # Create elapsed time timer
        self.elapsed_timer = QtCore.QElapsedTimer()
        
    def startProtocol(self):
        print "Starting protocol"
        protocol_ID = self.protocolListWidget.currentRow()
        command_name = self.protocol_commands[protocol_ID][0]
        command_duration = self.protocol_durations[protocol_ID][0]
        self.status = [protocol_ID, 0]

        if self.verbose:
            print "Starting " + self.protocol_names[protocol_ID]
        
        self.issueCommand(command_name, command_duration)
        
    def advanceProtocol(self):
        status = self.status
        protocol_ID = self.status[0]
        command_ID = self.status[1] + 1
        if command_ID < len(self.protocol_commands[protocol_ID]):
            command_name = self.protocol_commands[protocol_ID][command_ID]
            command_duration = self.protocol_durations[protocol_ID][command_ID]
            self.status = [protocol_ID, command_ID]
            self.issueCommand(command_name, command_duration)
        else:
            self.stopProtocol()
        
    def stopProtocol(self):
        self.status = [-1,-1]
        self.protocol_timer.stop()
        if self.verbose:
            print "Stopped Protocol"

    def issueCommand(self, command_name, command_duration=-1):
        self.issued_command = self.valveCommands.getCommandByName(command_name)
        self.command_ready_signal.emit()
        if self.verbose:
            print "Issued: " + command_name + ": " + str(command_duration) + " s"
            print self.issued_command
        if command_duration >= 0:
            self.protocol_timer.start(command_duration*1000)
 
    def loadProtocols(self, xml_file_path = ""):
        # Set Configuration XML (load if needed)
        if not xml_file_path:
            xml_file_path = QtGui.QFileDialog.getOpenFileName(self, "Open File", "\home")
        self.protocol_xml_path = xml_file_path
        
        # Parse XML
        self.parseProtocolXML()

        # Update GUI
        self.updateGUI()

        # Display if desired
        if self.verbose:
            self.printProtocols()
    def getCurrentCommand(self):
        return self.issued_command
    
    def getProtocolNames(self):
        return self.protocol_names

    def getNumProtocols(self):
        return self.num_protocols

    def getProtocolByName(self, command_name):
        try:
            command_ID = self.command_names.index(command_name)
            return self.commands[command_ID]
        except:
            print "Did not find " + command_name
            return [-1]*self.num_valves # Return no change command

    def parseProtocolXML(self):
        try:
            print "Loading: " + self.protocol_xml_path
            self.xml_tree = elementTree.parse(self.protocol_xml_path)
            self.valve_configuration = self.xml_tree.getroot()
        except:
            print "Valid xml file not loaded"
            return
        else:
            print "Loaded: " + self.protocol_xml_path

        # Clear previous commands
        self.protocol_names = []
        self.protocol_commands = []
        self.protocol_durations = []
        self.num_protocols = 0
        
        # Load commands
        for valve_protocols in self.valve_configuration.findall("valve_protocols"):
            protocol_list = valve_protocols.findall("protocol")
            for protocol in protocol_list:
                self.protocol_names.append(protocol.get("name"))
                new_protocol_commands = []
                new_protocol_durations = []
                for command in protocol.findall("command"):
                    new_protocol_durations.append(int(command.get("duration")))
                    new_protocol_commands.append(command.text)
                self.protocol_commands.append(new_protocol_commands)
                self.protocol_durations.append(new_protocol_durations)

        # Record number of configs
        self.num_protocols = len(self.protocol_names)
        print self.protocol_names
        
    def printProtocols(self):
        print "Current protocols:"
        for protocol_ID in range(self.num_protocols):
            print self.protocol_names[protocol_ID]
            for command_ID, command in enumerate(self.protocol_commands[protocol_ID]):
                textString = "    " + command + ": "
                textString += str(self.protocol_durations[protocol_ID][command_ID]) + " s"
                print textString

    def createGUI(self):
        self.groupBox = QtGui.QGroupBox()
        self.groupBox.setTitle("Valve Protocols")
        self.groupBoxLayout = QtGui.QVBoxLayout(self.groupBox)

        self.fileLabel = QtGui.QLabel()
        self.fileLabel.setText("")

        self.protocolListWidget = QtGui.QListWidget()
        self.protocolListWidget.currentItemChanged.connect(self.updateProtocolDescriptor)
        
        self.currentProtocolGroupBox = QtGui.QGroupBox()
        self.currentProtocolGroupBox.setTitle("Current Protocol")
        self.currentProtocolGroupBoxLayout = QtGui.QVBoxLayout(self.currentProtocolGroupBox)

        self.currentProtocolDescription = QtGui.QLabel()
        self.currentProtocolDescription.setText("")
        self.currentProtocolGroupBoxLayout.addWidget(self.currentProtocolDescription)
        
        self.startProtocolButton = QtGui.QPushButton("Start Protocol")
        self.startProtocolButton.clicked.connect(self.startProtocol)
        self.stopProtocolButton = QtGui.QPushButton("Stop Protocol")
        self.stopProtocolButton.clicked.connect(self.stopProtocol)
        
        self.protocolStatusGroupBox = QtGui.QGroupBox()
        self.protocolStatusGroupBox.setTitle("Command In Progress")
        self.protocolStatusGroupBoxLayout = QtGui.QVBoxLayout(self.protocolStatusGroupBox)
        
        self.protocolStatusText = QtGui.QLabel()
        self.protocolStatusText.setText("")
        self.protocolStatusGroupBoxLayout.addWidget(self.protocolStatusText)

        self.groupBoxLayout.addWidget(self.fileLabel)
        self.groupBoxLayout.addWidget(self.protocolListWidget)
        self.groupBoxLayout.addWidget(self.currentProtocolGroupBox)
        self.groupBoxLayout.addWidget(self.startProtocolButton)
        self.groupBoxLayout.addWidget(self.stopProtocolButton)
        self.groupBoxLayout.addWidget(self.protocolStatusText)
        self.groupBoxLayout.addStretch(1)

        # add all main to the main vLayout
        self.mainLayout = QtGui.QVBoxLayout()
        self.mainLayout.addWidget(self.groupBox)
        self.mainLayout.addWidget(self.valveCommands.groupBox)

        self.mainWidget = QtGui.QGroupBox()
        self.mainWidget.setLayout(self.mainLayout)
        
        # Menu items (may not be used)
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.closeEvent)
        
    def updateGUI(self):
        self.protocolListWidget.clear() # Remove previous items
        for name in self.protocol_names:
            self.protocolListWidget.addItem(name)

        if len(self.protocol_names) > 0:
            self.protocolListWidget.setCurrentRow(0) # Set to default

        self.fileLabel.setText(self.protocol_xml_path)
        
    def updateProtocolDescriptor(self):
        protocol_ID = self.protocolListWidget.currentRow()
        current_protocol_name = self.protocol_names[protocol_ID]
        current_protocol_commands = self.protocol_commands[protocol_ID]
        current_protocol_durations = self.protocol_durations[protocol_ID]
        
        text_string = current_protocol_name + "\n"
        for ID in range(len(current_protocol_commands)):
            text_string += current_protocol_commands[ID]
            text_string += ": "
            text_string += str(current_protocol_durations[ID]) + " s"
            text_string += "\n"

        self.currentProtocolDescription.setText(text_string)
        
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.valveProtocols = ValveProtocols(verbose = True)
                                  
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.valveProtocols.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Valve Protocols")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    sys.exit(app.exec_())

#!/usr/bin/python
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt4 import QtCore, QtGui
from valveCommands import ValveCommands

class ValveProtocols(QtGui.QMainWindow):
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
        
        # Create Valve Commands
        self.valveCommands = ValveCommands(xml_file_path = self.command_xml_path,
                                           verbose = self.verbose)
        # Create GUI
        self.createGUI()

        # Load Configurations
        self.loadProtocols(xml_file_path = self.protocol_xml_path)

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

##    def getCommandByIndex(self, command_ID):
##        try:
##            return self.commands[command_ID]
##        except:
##            print "Invalvid command index: " + command_ID
##            return [-1]*self.num_valves # return default
##
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
        
        self.sendProtocolButton = QtGui.QPushButton("Execute Protocol")
        #self.sendCommandButton.clicked.connect()

        self.protocolStatusGroupBox = QtGui.QGroupBox()
        self.protocolStatusGroupBox.setTitle("Command In Progress")
        self.protocolStatusGroupBoxLayout = QtGui.QVBoxLayout(self.protocolStatusGroupBox)
        
        self.protocolStatusText = QtGui.QLabel()
        self.protocolStatusText.setText("")
        self.protocolStatusGroupBoxLayout.addWidget(self.protocolStatusText)

        self.groupBoxLayout.addWidget(self.fileLabel)
        self.groupBoxLayout.addWidget(self.protocolListWidget)
        self.groupBoxLayout.addWidget(self.currentProtocolGroupBox)
        self.groupBoxLayout.addWidget(self.sendProtocolButton)
        self.groupBoxLayout.addWidget(self.protocolStatusText)
        self.groupBoxLayout.addStretch(1)

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
        current_ID = self.protocolListWidget.currentRow()
        current_protocol_name = self.protocol_names[current_ID]
        current_protocol_commands = self.protocol_commands[current_ID]
        current_protocol_durations = self.protocol_durations[current_ID]
        
        text_string = current_protocol_name + "\n"
        for ID in range(len(current_protocol_commands)):
            text_string += current_protocol_commands[ID]
            text_string += ": "
            text_string += str(current_protocol_durations[ID]) + " s"
            text_string += "\n"

        self.currentProtocolDescription.setText(text_string)
##
##    def transmitCommandIndex(self):
##        current_ID = self.commandListWidget.currentRow()
##        self.change_command_signal.emit(current_ID)
##        if self.verbose:
##            print "Emit: " + str(current_ID) + " " + self.command_names[current_ID]

class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.valveProtocols = ValveProtocols(verbose = True)
        
        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.valveProtocols.groupBox)
        self.mainLayout.addWidget(self.valveProtocols.valveCommands.groupBox)
                                  
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Valve Protocols")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

        # Create file menu
##        menubar = self.menuBar()
##        file_menu = menubar.addMenu("File")
##
##        exit_action = QtGui.QAction("Exit", self)
##        exit_action.setShortcut("Ctrl+Q")
##        exit_action.triggered.connect(self.closeEvent)
##
##        file_menu.addAction(exit_action)
##        file_menu.addAction(self.valve_chain_commands.load_commands_action)

##    def closeEvent(self, event):
##        self.valve_chain_commands.close()
##        self.close()
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    sys.exit(app.exec_())

#!/usr/bin/python
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt4 import QtCore, QtGui

class ValveCommands(QtGui.QMainWindow):

    change_command_signal = QtCore.pyqtSignal(int)
    
    def __init__(self,
                 xml_file_path="default_config.xml",
                 verbose = False):
        super(ValveCommands, self).__init__()

        # Initialize internal attributes
        self.verbose = verbose
        self.file_name = xml_file_path
        self.command_names = []
        self.commands = []
        self.num_commands = 0
        self.num_valves = 0
        
        # Create GUI
        self.createGUI()

        # Load Configurations
        self.loadCommands(xml_file_path = self.file_name)

    def loadCommands(self, xml_file_path = ""):
        # Set Configuration XML (load if needed)
        if not xml_file_path:
            xml_file_path = QtGui.QFileDialog.getOpenFileName(self, "Open File", "\home")
        self.file_name = xml_file_path
        
        # Parse XML
        self.parseCommandXML()

        # Update GUI
        self.updateGUI()

        # Display if desired
        if self.verbose:
            self.printCommands()
        
    def getCommandNames(self):
        return self.command_names

    def getNumberOfValves(self):
        return self.default_num_valves

    def getNumCommands(self):
        return self.num_commands

    def getCommandByName(self, command_name):
        try:
            command_ID = self.command_names.index(command_name)
            return self.commands[command_ID]
        except:
            print "Did not find " + command_name
            return [-1]*self.num_valves # Return no change command

    def getCommandByIndex(self, command_ID):
        try:
            return self.commands[command_ID]
        except:
            print "Invalvid command index: " + command_ID
            return [-1]*self.num_valves # return default

    def parseCommandXML(self):
        try:
            print "Loading: " + self.file_name
            self.xml_tree = elementTree.parse(self.file_name)
            self.valve_configuration = self.xml_tree.getroot()
        except:
            print "Valid xml file not loaded"
            return
        else:
            print "Loaded: " + self.file_name

        # Clear previous commands
        self.command_names = []
        self.commands = []
        self.num_commands = 0

        # Load number of valves
        self.num_valves = int(self.valve_configuration.get("num_valves"))
        if not (self.num_valves>0):
            print "Number of valves not specified"
        
        # Load commands
        for valve_command in self.valve_configuration.findall("valve_commands"):
            print valve_command
            command_list = valve_command.findall("valve_cmd")
            for command in command_list:
                new_command = [-1]*self.num_valves # make copy to initialize config with default
                for valve_pos in command.findall("valve_pos"):
                    valve_ID = int(valve_pos.get("valve_ID")) - 1
                    port_ID = int(valve_pos.get("port_ID")) - 1
                    if valve_ID < self.num_valves:
                        new_command[valve_ID] = port_ID
                    else:
                        print "Valve out of range on command: " + command.get("name")

                # Add command
                self.commands.append(new_command)
                self.command_names.append(command.get("name"))

        # Record number of configs
        self.num_commands = len(self.command_names)
        
    def printCommands(self):
        print "Current commands:"
        for command_ID in range(self.num_commands):
            print self.command_names[command_ID]
            for valve_ID in range(self.num_valves):
                port_ID = self.commands[command_ID][valve_ID]
                textString = "    " + "Valve " + str(valve_ID + 1)
                if port_ID >= 0:
                    textString += " configured to port " + str(port_ID+1)
                else:
                    textString += " configured to not change"

    def setActiveCommand(self, command_name):
        command_ID = self.command_names.index(command_name)
        self.commandListWidget.setCurrentRow(command_ID)
        self.updateCommandDisplay()
    
    def createGUI(self):
        self.groupBox = QtGui.QGroupBox()
        self.groupBox.setTitle("Valve Commands")
        self.groupBoxLayout = QtGui.QVBoxLayout(self.groupBox)

        self.fileLabel = QtGui.QLabel()
        self.fileLabel.setText("")

        self.commandListWidget = QtGui.QListWidget()
        self.commandListWidget.currentItemChanged.connect(self.updateCommandDisplay)
        
        self.sendCommandButton = QtGui.QPushButton("Send Command")
        self.sendCommandButton.clicked.connect(self.transmitCommandIndex)

        self.currentCommandGroupBox = QtGui.QGroupBox()
        self.currentCommandGroupBox.setTitle("Current Command")
        self.currentCommandGroupBoxLayout = QtGui.QVBoxLayout(self.currentCommandGroupBox)

        self.currentCommandLabel = QtGui.QLabel()
        self.currentCommandLabel.setText("")
        self.currentCommandGroupBoxLayout.addWidget(self.currentCommandLabel)

        self.groupBoxLayout.addWidget(self.fileLabel)
        self.groupBoxLayout.addWidget(self.commandListWidget)
        self.groupBoxLayout.addWidget(self.sendCommandButton)
        self.groupBoxLayout.addWidget(self.currentCommandGroupBox)

        self.groupBoxLayout.addStretch(1)

        # Menu items (may not be used)
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.closeEvent)

        self.load_commands_action = QtGui.QAction("Load new commands", self)
        self.load_commands_action.setShortcut("Ctrl+O")
        self.load_commands_action.triggered.connect(self.loadCommands)
        self.load_commands_action_menu_name = "File"
        
    def updateGUI(self):
        self.commandListWidget.clear() # Remove previous items
        for name in self.command_names:
            self.commandListWidget.addItem(name)

        if len(self.command_names) > 0:
            self.commandListWidget.setCurrentRow(0) # Set to default
        self.fileLabel.setText(self.file_name)

    def updateCommandDisplay(self):
        current_ID = self.commandListWidget.currentRow()
        current_command_name = self.command_names[current_ID]
        current_command = self.commands[current_ID]

        text_string = current_command_name + "\n"
        for valve_ID, port_ID in enumerate(current_command):
            text_string += "Valve " + str(valve_ID+1)
            if port_ID == -1:
                text_string += ": No Change "
            else:
                text_string += ": Port " + str(port_ID+1)
            text_string += "\n"

        self.currentCommandLabel.setText(text_string)

    def transmitCommandIndex(self):
        current_ID = self.commandListWidget.currentRow()
        self.change_command_signal.emit(current_ID)
        if self.verbose:
            print "Emit: " + str(current_ID) + " " + self.command_names[current_ID]

class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.valve_chain_commands = ValveCommands(verbose = True)
        
        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.valve_chain_commands.groupBox)
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Valve Chain Commands")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

        # Create file menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.closeEvent)

        file_menu.addAction(exit_action)
        file_menu.addAction(self.valve_chain_commands.load_commands_action)

    def closeEvent(self, event):
        self.valve_chain_commands.close()
        self.close()
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    sys.exit(app.exec_())

#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A class to load, parse, and control predefined valve commands, i.e predefined
# changes to the port configurations of a valve chain. 
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/28/13
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt5 import QtCore, QtGui, QtWidgets

# ----------------------------------------------------------------------------------------
# ValveCommands Class Definition
# ----------------------------------------------------------------------------------------
class ValveCommands(QtWidgets.QMainWindow):

    # Define custom signal
    change_command_signal = QtCore.pyqtSignal(str)
    
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

    # ------------------------------------------------------------------------------------
    # Create display and control widgets
    # ------------------------------------------------------------------------------------
    def close(self):
        if self.verbose: print("Closing valve commands")

    # ------------------------------------------------------------------------------------
    # Create display and control widgets
    # ------------------------------------------------------------------------------------
    def createGUI(self):
        self.mainWidget = QtWidgets.QGroupBox()
        self.mainWidget.setTitle("Valve Commands")
        self.mainWidgetLayout = QtWidgets.QVBoxLayout(self.mainWidget)

        self.fileLabel = QtWidgets.QLabel()
        self.fileLabel.setText("")

        self.commandListWidget = QtWidgets.QListWidget()
        self.commandListWidget.currentItemChanged.connect(self.updateCommandDisplay)
        
        self.sendCommandButton = QtWidgets.QPushButton("Send Command")
        self.sendCommandButton.clicked.connect(self.transmitCommandIndex)

        self.currentCommandGroupBox = QtWidgets.QGroupBox()
        self.currentCommandGroupBox.setTitle("Current Command")
        self.currentCommandGroupBoxLayout = QtWidgets.QVBoxLayout(self.currentCommandGroupBox)

        self.currentCommandLabel = QtWidgets.QLabel()
        self.currentCommandLabel.setText("")
        self.currentCommandGroupBoxLayout.addWidget(self.currentCommandLabel)

        self.mainWidgetLayout.addWidget(self.fileLabel)
        self.mainWidgetLayout.addWidget(self.commandListWidget)
        self.mainWidgetLayout.addWidget(self.sendCommandButton)
        self.mainWidgetLayout.addWidget(self.currentCommandGroupBox)

        self.mainWidgetLayout.addStretch(1)

        # Menu items (may not be used)
        self.exit_action = QtWidgets.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.closeEvent)

        self.load_commands_action = QtWidgets.QAction("Load New Commands", self)
        self.load_commands_action.triggered.connect(self.loadCommands)
        self.load_commands_action_menu_name = "File"

    # ------------------------------------------------------------------------------------
    # Return a command indexed with its ID (0,1,2,...)
    # ------------------------------------------------------------------------------------        
    def getCommandByIndex(self, command_ID):
        try:
            return self.commands[command_ID]
        except:
            print("Invalvid command index: " + command_ID)
            return [-1]*self.num_valves # return default

    # ------------------------------------------------------------------------------------
    # Return a command indexed by its name
    # ------------------------------------------------------------------------------------        
    def getCommandByName(self, command_name):
        try:
            command_ID = self.command_names.index(command_name)
            return self.commands[command_ID]
        except:
            print("Did not find " + command_name)
            return [-1]*self.num_valves # Return no change command

    # ------------------------------------------------------------------------------------
    # Return the names of the current defined commands
    # ------------------------------------------------------------------------------------        
    def getCommandNames(self):
        return self.command_names

    # ------------------------------------------------------------------------------------
    # Return the number of defined commands
    # ------------------------------------------------------------------------------------        
    def getNumCommands(self):
        return self.num_commands

    # ------------------------------------------------------------------------------------
    # Return the number of valves in the defined commands:
    #   could be different than in the chain
    # ------------------------------------------------------------------------------------        
    def getNumberOfValves(self):
        return self.default_num_valves

    # ------------------------------------------------------------------------------------
    # Load and parse a XML file with defined commands
    # ------------------------------------------------------------------------------------
    def loadCommands(self, xml_file_path = ""):
        # Set Configuration XML (load if needed)
        if not xml_file_path:
            xml_file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "\home")[0]
            if not os.path.isfile(xml_file_path):
                xml_file_path = "default_config.xml"
                print("Not a valid path. Restoring: " + xml_file_path)
        self.file_name = xml_file_path
        
        # Parse XML
        self.parseCommandXML()

        # Update GUI
        self.updateGUI()

        # Display if desired
        if self.verbose:
            self.printCommands()

    # ------------------------------------------------------------------------------------
    # Parse the command xml file
    # ------------------------------------------------------------------------------------        
    def parseCommandXML(self):
        # Try loading file
        try:
            print("Parsing for commands: " + self.file_name)
            self.xml_tree = elementTree.parse(self.file_name)
            self.kilroy_configuration = self.xml_tree.getroot()
        except:
            print("Valid xml file not loaded")
            return

        # Clear previous commands
        self.command_names = []
        self.commands = []
        self.num_commands = 0

        # Load number of valves
        self.num_valves = int(self.kilroy_configuration.get("num_valves"))
        if not (self.num_valves>0):
            print("Number of valves not specified")
        
        # Load commands
        for valve_command in self.kilroy_configuration.findall("valve_commands"):
            command_list = valve_command.findall("valve_cmd")
            for command in command_list:
                new_command = [-1]*self.num_valves # make copy to initialize config with default
                for valve_pos in command.findall("valve_pos"):
                    valve_ID = int(valve_pos.get("valve_ID")) - 1
                    port_ID = int(valve_pos.get("port_ID")) - 1
                    if valve_ID < self.num_valves:
                        new_command[valve_ID] = port_ID
                    else:
                        print("Valve out of range on command: " + command.get("name"))

                # Add command
                self.commands.append(new_command)
                self.command_names.append(command.get("name"))

        # Record number of configs
        self.num_commands = len(self.command_names)

    # ------------------------------------------------------------------------------------
    # Display loaded commands
    # ------------------------------------------------------------------------------------                
    def printCommands(self):
        print("Current commands:")
        for command_ID in range(self.num_commands):
            print(self.command_names[command_ID])
            for valve_ID in range(self.num_valves):
                port_ID = self.commands[command_ID][valve_ID]
                textString = "    " + "Valve " + str(valve_ID + 1)
                if port_ID >= 0:
                    textString += " configured to port " + str(port_ID+1)
                else:
                    textString += " configured to not change"

    # ------------------------------------------------------------------------------------
    # Update active command on GUI
    # ------------------------------------------------------------------------------------                
    def setActiveCommand(self, command_name):
        command_ID = self.command_names.index(command_name)
        self.commandListWidget.setCurrentRow(command_ID)
        self.updateCommandDisplay()

    # ------------------------------------------------------------------------------------
    # Control active state of GUI elements
    # ------------------------------------------------------------------------------------                
    def setEnabled(self, is_enabled):
        self.sendCommandButton.setEnabled(is_enabled)

    # ------------------------------------------------------------------------------------
    # Transmit the index of the desired command to send (if triggered)
    # ------------------------------------------------------------------------------------
    def transmitCommandIndex(self):
        current_ID = self.commandListWidget.currentRow()
        self.change_command_signal.emit(self.command_names[current_ID])

    # ------------------------------------------------------------------------------------
    # Display specifics of selected command
    # ------------------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------------------
    # Update GUI
    # ------------------------------------------------------------------------------------        
    def updateGUI(self):
        self.commandListWidget.clear() # Remove previous items
        for name in self.command_names:
            self.commandListWidget.addItem(name)

        if len(self.command_names) > 0:
            self.commandListWidget.setCurrentRow(0) # Set to default

        drive, path_and_file = os.path.splitdrive(str(self.file_name)) # Kludge to convert QString to str
        path_name, file_name = os.path.split(str(path_and_file))
        self.fileLabel.setText(file_name)
        self.fileLabel.setToolTip(self.file_name) 

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------
class StandAlone(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.valve_chain_commands = ValveCommands(verbose = True)
        
        # main layout

        # add all main to the main vLayout
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.mainLayout.addWidget(self.valve_chain_commands.mainWidget)

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
        
    # ------------------------------------------------------------------------------------
    # Detect close event
    # ------------------------------------------------------------------------------------    
    def closeEvent(self, event):
        self.valve_chain_commands.close()
        self.close()

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------                
if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    sys.exit(app.exec_())

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

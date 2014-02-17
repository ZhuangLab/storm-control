#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A class to load and parse predefined pump commands. 
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 2/16/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt4 import QtCore, QtGui

# ----------------------------------------------------------------------------------------
# PumpCommands Class Definition
# ----------------------------------------------------------------------------------------
class PumpCommands(QtGui.QMainWindow):

    # Define custom signal
    change_command_signal = QtCore.pyqtSignal(str)
    
    def __init__(self,
                 xml_file_path="default_config.xml",
                 verbose = False):
        super(PumpCommands, self).__init__()

        # Initialize internal attributes
        self.verbose = verbose
        self.file_name = xml_file_path
        self.command_names = []
        self.commands = []
        self.num_commands = 0
        self.num_pumps = 0
        
        # Create GUI
        self.createGUI()

        # Load Configurations
        self.loadCommands(xml_file_path = self.file_name)

    # ------------------------------------------------------------------------------------
    # Create display and control widgets
    # ------------------------------------------------------------------------------------
    def close(self):
        if self.verbose: print "Closing pump commands"

    # ------------------------------------------------------------------------------------
    # Create display and control widgets
    # ------------------------------------------------------------------------------------
    def createGUI(self):
        self.mainWidget = QtGui.QGroupBox()
        self.mainWidget.setTitle("Pump Commands")
        self.mainWidgetLayout = QtGui.QVBoxLayout(self.mainWidget)

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

        self.mainWidgetLayout.addWidget(self.fileLabel)
        self.mainWidgetLayout.addWidget(self.commandListWidget)
        self.mainWidgetLayout.addWidget(self.sendCommandButton)
        self.mainWidgetLayout.addWidget(self.currentCommandGroupBox)

        self.mainWidgetLayout.addStretch(1)

        # Menu items (may not be used)
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.closeEvent)

        self.load_commands_action = QtGui.QAction("Load New Commands", self)
        self.load_commands_action.triggered.connect(self.loadCommands)
        self.load_commands_action_menu_name = "File"

    # ------------------------------------------------------------------------------------
    # Return a command indexed with its ID (0,1,2,...)
    # ------------------------------------------------------------------------------------        
    def getCommandByIndex(self, command_ID):
        try:
            return self.commands[command_ID]
        except:
            print "Invalvid command index: " + command_ID
            return [-1]*self.num_valves # return default

    # ------------------------------------------------------------------------------------
    # Return a command indexed by its name
    # ------------------------------------------------------------------------------------        
    def getCommandByName(self, command_name):
        try:
            command_ID = self.command_names.index(command_name)
            return self.commands[command_ID]
        except:
            print "Did not find " + command_name
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
    # Load and parse a XML file with defined commands
    # ------------------------------------------------------------------------------------
    def loadCommands(self, xml_file_path = ""):
        # Set Configuration XML (load if needed)
        if not xml_file_path:
            xml_file_path = QtGui.QFileDialog.getOpenFileName(self, "Open File", "\home")
            if not os.path.isfile(xml_file_path):
                xml_file_path = "default_config.xml"
                print "Not a valid path. Restoring: " + xml_file_path
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
            print "Parsing for commands: " + self.file_name
            self.xml_tree = elementTree.parse(self.file_name)
            self.kilroy_configuration = self.xml_tree.getroot()
        except:
            print "Valid xml file not loaded"
            return

        # Clear previous commands
        self.command_names = []
        self.commands = []
        self.num_commands = 0

        # Load number of valves
        self.num_pumps = int(self.kilroy_configuration.get("num_pumps"))
        if not (self.num_pumps>0):
            print "Number of pumps not specified"
        
        # Load commands
        for pump_command in self.kilroy_configuration.findall("pump_commands"):
            command_list = pump_command.findall("pump_cmd")
            for command in command_list:
                for pump_config in command.findall("pump_config"):
                    speed = float(pump_config.get("speed"))
                    direction = pump_config.get("direction")
                    if speed < 0.00 or speed > 48.0:
                        speed = 0.0
                        direction = "Stopped" # Flag for stopped flow
                    direction = {"Forward": "Forward", "Reverse": "Reverse"}.get(direction, "Stopped")
                    
                # Add command
                self.commands.append([direction, speed])
                self.command_names.append(command.get("name"))

        # Record number of configs
        self.num_commands = len(self.command_names)

    # ------------------------------------------------------------------------------------
    # Display loaded commands
    # ------------------------------------------------------------------------------------                
    def printCommands(self):
        print "Current commands:"
        for command_ID in range(self.num_commands):
            print self.command_names[command_ID]
            direction = self.commands[command_ID][0]
            speed = self.commands[command_ID][1]
            text_string = "    " + "Flow Direction: " + direction + "\n"
            text_string += "    " + "Speed: " + str(speed) +"\n"
            print text_string

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
        text_string += "Flow Direction: " + current_command[0] + "\n"
        text_string += "Flow Speed: " + str(current_command[1]) + "\n"
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
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.pump_commands = PumpCommands(verbose = True)
        
        # main layout

        # add all main to the main vLayout
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.mainLayout.addWidget(self.pump_commands.mainWidget)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Pump Commands")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

        # Create file menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        exit_action = QtGui.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.closeEvent)

        file_menu.addAction(exit_action)
        file_menu.addAction(self.pump_commands.load_commands_action)
        
    # ------------------------------------------------------------------------------------
    # Detect close event
    # ------------------------------------------------------------------------------------    
    def closeEvent(self, event):
        self.pump_commands.close()
        self.close()

# ----------------------------------------------------------------------------------------
# Test/Demo of Classs
# ----------------------------------------------------------------------------------------                
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
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

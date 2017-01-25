#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A class to load, parse, and control predefined kilroy protocols, i.e.
# collections of predefined valve or pump configurations and a defined
# duration to wait before setting the next configuration. This class also
# provides a basic I/O GUI to interface with protocols. 
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 2/15/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import os
import xml.etree.ElementTree as elementTree
from PyQt5 import QtCore, QtGui, QtWidgets
from storm_control.fluidics.valves.valveCommands import ValveCommands
from storm_control.fluidics.pumps.pumpCommands import PumpCommands

# ----------------------------------------------------------------------------------------
# KilroyProtocols Class Definition
# ----------------------------------------------------------------------------------------
class KilroyProtocols(QtWidgets.QMainWindow):

    # Define custom command ready signal
    command_ready_signal = QtCore.pyqtSignal() # A command is ready to be issued
    status_change_signal = QtCore.pyqtSignal() # A protocol status change occured
    completed_protocol_signal = QtCore.pyqtSignal(object) # Name of completed protocol
        
    def __init__(self,
                 protocol_xml_path = "default_config.xml",
                 command_xml_path = "default_config.xml",
                 verbose = False):
        super(KilroyProtocols, self).__init__()

        # Initialize internal attributes
        self.verbose = verbose
        self.protocol_xml_path = protocol_xml_path
        self.command_xml_path = command_xml_path
        self.protocol_names = []
        self.protocol_commands = [] # [Instrument Type, command_info]
        self.protocol_durations = []
        self.num_protocols = 0
        self.status = [-1, -1] # Protocol ID, command ID within protocol
        self.issued_command = []
        self.received_message = None

        print("----------------------------------------------------------------------")
        
        # Create instance of ValveCommands class
        self.valveCommands = ValveCommands(xml_file_path = self.command_xml_path,
                                           verbose = self.verbose)

        # Connect valve command issue signal
        self.valveCommands.change_command_signal.connect(self.issueValveCommand)

        # Create instance of PumpCommands class
        self.pumpCommands = PumpCommands(xml_file_path = self.command_xml_path,
                                         verbose = self.verbose)

        # Connect pump commands issue signal
        self.pumpCommands.change_command_signal.connect(self.issuePumpCommand)
        
        # Create GUI
        self.createGUI()

        # Load configurations
        self.loadProtocols(xml_file_path = self.protocol_xml_path)

        # Create protocol timer--controls when commands are issued
        self.protocol_timer = QtCore.QTimer()
        self.protocol_timer.setSingleShot(True)
        self.protocol_timer.timeout.connect(self.advanceProtocol)

        # Create elapsed time timer--determines time between command calls
        self.elapsed_timer = QtCore.QElapsedTimer()
        self.poll_elapsed_time_timer = QtCore.QTimer()
        self.poll_elapsed_time_timer.setInterval(1000)
        self.poll_elapsed_time_timer.timeout.connect(self.updateElapsedTime)

    # ------------------------------------------------------------------------------------
    # Advance the protocol to the next command and issue it
    # ------------------------------------------------------------------------------------       
    def advanceProtocol(self):
        status = self.status
        protocol_ID = self.status[0]
        command_ID = self.status[1] + 1
        if command_ID < len(self.protocol_commands[protocol_ID]):
            command_name = self.protocol_commands[protocol_ID][command_ID]
            command_duration = self.protocol_durations[protocol_ID][command_ID]
            self.status = [protocol_ID, command_ID]
            self.issueCommand(command_name, command_duration)

            self.elapsed_timer.start()

            self.protocolDetailsList.setCurrentRow(command_ID)
        else:
            self.stopProtocol()

    # ------------------------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------------------------                                                
    def close(self):
        self.stopProtocol()
        if self.verbose: print("Closing valve protocols")
        self.valveCommands.close()
        
    # ------------------------------------------------------------------------------------
    # Create display and control widgets
    # ------------------------------------------------------------------------------------                                                
    def createGUI(self):
        self.mainWidget = QtWidgets.QGroupBox()
        self.mainWidget.setTitle("Protocols")
        self.mainWidgetLayout = QtWidgets.QVBoxLayout(self.mainWidget)

        self.fileLabel = QtWidgets.QLabel()
        self.fileLabel.setText("")

        self.protocolListWidget = QtWidgets.QListWidget()
        self.protocolListWidget.currentItemChanged.connect(self.updateProtocolDescriptor)

        self.elapsedTimeLabel = QtWidgets.QLabel()
        self.elapsedTimeLabel.setText("Elapsed Time: ")

        self.protocolDetailsList = QtWidgets.QListWidget()
        
        self.startProtocolButton = QtWidgets.QPushButton("Start Protocol")
        self.startProtocolButton.clicked.connect(self.startProtocolLocally)
        self.skipCommandButton = QtWidgets.QPushButton("Skip Command")
        self.skipCommandButton.clicked.connect(self.skipCommand)
        self.stopProtocolButton = QtWidgets.QPushButton("Stop Protocol")
        self.stopProtocolButton.clicked.connect(self.stopProtocol)
        
        self.protocolStatusGroupBox = QtWidgets.QGroupBox()
        self.protocolStatusGroupBox.setTitle("Command In Progress")
        self.protocolStatusGroupBoxLayout = QtWidgets.QVBoxLayout(self.protocolStatusGroupBox)
        
        self.mainWidgetLayout.addWidget(self.fileLabel)
        self.mainWidgetLayout.addWidget(self.protocolListWidget)
        self.mainWidgetLayout.addWidget(self.elapsedTimeLabel)
        self.mainWidgetLayout.addWidget(self.protocolDetailsList)
        self.mainWidgetLayout.addWidget(self.startProtocolButton)
        self.mainWidgetLayout.addWidget(self.skipCommandButton)
        self.mainWidgetLayout.addWidget(self.stopProtocolButton)
        self.mainWidgetLayout.addStretch(1)

        # Configure menu items
        self.load_fullconfig_action = QtWidgets.QAction("Load Full Configuration", self)
        self.load_fullconfig_action.triggered.connect(self.loadFullConfiguration)
        
        self.load_protocols_action = QtWidgets.QAction("Load New Protocols", self)
        self.load_protocols_action.triggered.connect(self.loadProtocols)

        self.load_commands_action = self.valveCommands.load_commands_action
        
        self.menu_names = ["File"]
        self.menu_items = [[self.load_fullconfig_action,
                            self.load_protocols_action,
                            self.load_commands_action]]

        # Disable buttons
        self.skipCommandButton.setEnabled(False)
        self.stopProtocolButton.setEnabled(False)

    # ------------------------------------------------------------------------------------
    # Return current command
    # ------------------------------------------------------------------------------------                                    
    def getCurrentCommand(self):
        return self.issued_command

    # ------------------------------------------------------------------------------------
    # Return the number of loaded protocols
    # ------------------------------------------------------------------------------------                                        
    def getNumProtocols(self):
        return self.num_protocols

    # ------------------------------------------------------------------------------------
    # Return protocol status
    # ------------------------------------------------------------------------------------                                        
    def getStatus(self):
        return self.status # [protocol_ID, command_ID] -1 = no active protocol

    # ------------------------------------------------------------------------------------
    # Return a protocol index by name
    # ------------------------------------------------------------------------------------                                        
    def getProtocolByName(self, command_name):
        try:
            command_ID = self.command_names.index(command_name)
            return self.commands[command_ID]
        except:
            print("Did not find " + command_name)
            return [-1]*self.num_valves # Return no change command

    # ------------------------------------------------------------------------------------
    # Return loaded protocol names
    # ------------------------------------------------------------------------------------                                        
    def getProtocolNames(self):
        return self.protocol_names

    # ------------------------------------------------------------------------------------
    # Issue a command: load current command, send command ready signal
    # ------------------------------------------------------------------------------------                       
    def issueCommand(self, command_data, command_duration=-1):
        if command_data[0] == "pump":
            self.issued_command = ["pump", self.pumpCommands.getCommandByName(command_data[1])]
        elif command_data[0] == "valve":
            self.issued_command = ["valve", self.valveCommands.getCommandByName(command_data[1])]
        if self.verbose:
            text = "Issued " + command_data[0] + ": " + command_data[1]
            if command_duration > 0:
                text += ": " + str(command_duration) + " s"
            print(text)
            
        self.command_ready_signal.emit()

        if command_duration >= 0:
            self.protocol_timer.start(command_duration*1000)

    # ------------------------------------------------------------------------------------
    # Handle Issue Command Request from Pump Commands
    # ------------------------------------------------------------------------------------                       
    def issuePumpCommand(self, command_name):
        self.issueCommand(["pump", command_name])

    # ------------------------------------------------------------------------------------
    # Handle Issue Command Request from Valve Commands
    # ------------------------------------------------------------------------------------                       
    def issueValveCommand(self, command_name):
        self.issueCommand(["valve", command_name])
        
    # ------------------------------------------------------------------------------------
    # Check to see if protocol name is in the list of protocols
    # ------------------------------------------------------------------------------------                       
    def isValidProtocol(self, protocol_name):
        try:
            self.protocol_names.index(protocol_name)
            return True
        except ValueError:
            if self.verbose:
                print(protocol_name + " is not a valid protocol")
            return False

    # ------------------------------------------------------------------------------------
    # Check to see if protocol name is in the list of protocols
    # ------------------------------------------------------------------------------------                       
    def isRunningProtocol(self):
        return self.status[0] >= 0

    # ------------------------------------------------------------------------------------
    # Load a protocol xml file
    # ------------------------------------------------------------------------------------                        
    def loadProtocols(self, xml_file_path = ""):
        # Set Configuration XML (load if needed)
        if not xml_file_path:
            xml_file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "\home")[0]
            if not os.path.isfile(xml_file_path):
                xml_file_path = "default_config.xml"
                print("Not a valid path. Restoring: " + xml_file_path)
                
        self.protocol_xml_path = xml_file_path
        
        # Parse XML
        self.parseProtocolXML()

        # Update GUI
        self.updateGUI()

        # Display if desired
        if self.verbose:
            self.printProtocols()
            
    # ------------------------------------------------------------------------------------
    # Short function to load both commands and protocols in a single file
    # ------------------------------------------------------------------------------------                        
    def loadFullConfiguration(self, xml_file_path = ""):
        print("----------------------------------------------------------------------")

        # Set Configuration XML (load if needed)
        if not xml_file_path:
            xml_file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "\home")[0]
            if not os.path.isfile(xml_file_path):
                xml_file_path = "default_config.xml"
                print("Not a valid path. Restoring: " + xml_file_path)

        self.protocol_xml_path = xml_file_path
        self.command_xml_path = xml_file_path

        # Update valveCommands
        self.valveCommands.loadCommands(xml_file_path = self.command_xml_path)

        # Update pumpCommands
        self.pumpCommands.loadCommands(xml_file_path = self.command_xml_path)
      
        # Parse XML
        self.parseProtocolXML()

        # Update GUI
        self.updateGUI()

        # Display if desired
        if self.verbose:
            self.printProtocols()

    # ------------------------------------------------------------------------------------
    # Parse loaded xml file: load protocols
    # ------------------------------------------------------------------------------------                                        
    def parseProtocolXML(self):
        try:
            print("Parsing for protocols: " + self.protocol_xml_path)
            self.xml_tree = elementTree.parse(self.protocol_xml_path)
            self.kilroy_configuration = self.xml_tree.getroot()
        except:
            print("Valid xml file not loaded")
            return

        # Clear previous commands
        self.protocol_names = []
        self.protocol_commands = []
        self.protocol_durations = []
        self.num_protocols = 0
        
        # Load commands
        for kilroy_protocols in self.kilroy_configuration.findall("kilroy_protocols"):
            protocol_list = kilroy_protocols.findall("protocol")
            for protocol in protocol_list:
                self.protocol_names.append(protocol.get("name"))
                new_protocol_commands = []
                new_protocol_durations = []
                for command in protocol: # Get all children
                    new_protocol_durations.append(int(command.get("duration")))
                    new_protocol_commands.append([command.tag,command.text]) # [Instrument Type, Command Name]
                    if (not (command.tag == "pump")) and (not (command.tag == "valve")):
                        print("Unknown command tag: " + command.tag)
                self.protocol_commands.append(new_protocol_commands)
                self.protocol_durations.append(new_protocol_durations)

        # Record number of configs
        self.num_protocols = len(self.protocol_names)

    # ------------------------------------------------------------------------------------
    # Display loaded protocols
    # ------------------------------------------------------------------------------------                                                
    def printProtocols(self):
        print("Current protocols:")
        for protocol_ID in range(self.num_protocols):
            print(self.protocol_names[protocol_ID])
            for command_ID, command in enumerate(self.protocol_commands[protocol_ID]):
                textString = "    " + command[0] + ": " + command[1] + ": "
                textString += str(self.protocol_durations[protocol_ID][command_ID]) + " s"
                print(textString)
                
    # ------------------------------------------------------------------------------------
    # Display loaded protocols
    # ------------------------------------------------------------------------------------                                                
    def requiredTime(self, protocol_name):
        protocol_ID = self.protocol_names.index(protocol_name)
        total_time = 0.0
        for time in self.protocol_durations[protocol_ID]:
            total_time += time

        return total_time
        
    # ------------------------------------------------------------------------------------
    # Initialize and start a protocol and issue first command
    # ------------------------------------------------------------------------------------
    def skipCommand(self):
        self.protocol_timer.stop()
        self.advanceProtocol()

    # ------------------------------------------------------------------------------------
    # Initialize and start a protocol and issue first command
    # ------------------------------------------------------------------------------------
    def startProtocol(self):
        protocol_ID = self.protocolListWidget.currentRow()
        
        # Get first command in protocol
        command_data = self.protocol_commands[protocol_ID][0]
        command_duration = self.protocol_durations[protocol_ID][0]

        # Set protocol status: [protocol_ID, command_ID]
        self.status = [protocol_ID, 0]
        self.status_change_signal.emit() # emit status change signal
        
        if self.verbose:
            print("Starting " + self.protocol_names[protocol_ID])

        # Issue command signal
        self.issueCommand(command_data, command_duration)
        
        # Start elapsed time timer
        self.elapsed_timer.start()
        self.poll_elapsed_time_timer.start()

        # Change enable status of GUI items
        self.startProtocolButton.setEnabled(False)
        self.skipCommandButton.setEnabled(True)
        self.stopProtocolButton.setEnabled(True)
        self.protocolListWidget.setEnabled(False)
        self.protocolDetailsList.setCurrentRow(0)
        self.valveCommands.setEnabled(False)
        self.pumpCommands.setEnabled(False)
        
    # ------------------------------------------------------------------------------------
    # Initialize and start a protocol specified by name
    # ------------------------------------------------------------------------------------
    def startProtocolByName(self, protocol_name):
        if self.isValidProtocol(protocol_name):
            if self.isRunningProtocol():
                if self.verbose:
                    print("Stopped In Progress: " + self.protocol_names[self.status[0]])
                self.stopProtocol() # Abort protocol in progress

            # Find protocol and set as active element 
            protocol_ID = self.protocol_names.index(protocol_name)
            self.protocolListWidget.setCurrentRow(protocol_ID)

            # Run protocol
            self.startProtocol()

    # ------------------------------------------------------------------------------------
    # Handle the local start button
    # ------------------------------------------------------------------------------------
    def startProtocolLocally(self):
        # Run protocol
        self.received_message = None # Remove existing messages
        self.startProtocol()

    # ------------------------------------------------------------------------------------
    # Initialize and start a protocol specified by a TCP message
    # ------------------------------------------------------------------------------------
    def startProtocolRemotely(self, message):
        protocol_name = message.getData("name")
        if self.isValidProtocol(protocol_name):
            if self.isRunningProtocol():
                if self.verbose:
                    print("Stopped In Progress: " + self.protocol_names[self.status[0]])
                self.stopProtocol() # Abort protocol in progress

            # Find protocol and set as active element 
            protocol_ID = self.protocol_names.index(protocol_name)
            self.protocolListWidget.setCurrentRow(protocol_ID)

            # Run protocol
            self.received_message = message
            self.startProtocol()
            
    # ------------------------------------------------------------------------------------
    # Stop a running protocol either on completion or early
    # ------------------------------------------------------------------------------------               
    def stopProtocol(self):
        # Get name of current protocol
        if self.status[0] >= 0:
            if self.verbose: print("Stopped Protocol")
            self.completed_protocol_signal.emit(self.received_message)
        
        # Reset status and emit status change signal
        self.status = [-1,-1]
        self.status_change_signal.emit()
        self.received_message = None
        
        # Stop timer
        self.protocol_timer.stop()

        # Re-enable GUI
        self.startProtocolButton.setEnabled(True)
        self.protocolListWidget.setEnabled(True)
        self.skipCommandButton.setEnabled(False)
        self.stopProtocolButton.setEnabled(False)
        self.valveCommands.setEnabled(True)
        self.pumpCommands.setEnabled(True)
        
        # Unselect all
        self.protocolDetailsList.setCurrentRow(0)
        self.protocolDetailsList.item(0).setSelected(False)
    
        # Stop timers
        self.poll_elapsed_time_timer.stop()
        self.elapsedTimeLabel.setText("Elapsed Time:")

    # ------------------------------------------------------------------------------------
    # Display time elapsed since previous command was issued
    # ------------------------------------------------------------------------------------                       
    def updateElapsedTime(self):
        ms_count = self.elapsed_timer.elapsed()
        elapsed_seconds = int ( float(ms_count) / float(1000) )
        
        text_string = "Elapsed Time: "
        text_string += str(elapsed_seconds)
        text_string += " s"
        self.elapsedTimeLabel.setText(text_string)

    # ------------------------------------------------------------------------------------
    # Update GUI based on protocols
    # ------------------------------------------------------------------------------------                                                
    def updateGUI(self):
        self.protocolListWidget.clear() # Remove previous items
        for name in self.protocol_names:
            self.protocolListWidget.addItem(name)

        if len(self.protocol_names) > 0:
            self.protocolListWidget.setCurrentRow(0) # Set to default

        drive, path_and_file = os.path.splitdrive(str(self.protocol_xml_path))
        path_name, file_name = os.path.split(str(path_and_file))
        self.fileLabel.setText(file_name)
        self.fileLabel.setToolTip(self.protocol_xml_path)
        
    # ------------------------------------------------------------------------------------
    # Update protocol description widget
    # ------------------------------------------------------------------------------------                                                        
    def updateProtocolDescriptor(self):
        protocol_ID = self.protocolListWidget.currentRow()
        current_protocol_name = self.protocol_names[protocol_ID]
        current_protocol_commands = self.protocol_commands[protocol_ID]
        current_protocol_durations = self.protocol_durations[protocol_ID]

        self.protocolDetailsList.clear()
        for ID in range(len(current_protocol_commands)):
            text_string = current_protocol_commands[ID][0]
            text_string += ": "
            text_string += current_protocol_commands[ID][1]
            text_string += ": "
            text_string += str(current_protocol_durations[ID]) + " s"

            wid = QtWidgets.QListWidgetItem(text_string)
            wid.setFlags(wid.flags() & QtCore.Qt.ItemIsSelectable)
            self.protocolDetailsList.insertItem(ID, wid)

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------                                                                
class StandAlone(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.kilroyProtocols = KilroyProtocols(verbose = True)
                                  
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QGridLayout(self.centralWidget)
        self.mainLayout.addWidget(self.kilroyProtocols.mainWidget,0,0,1,2)
        self.mainLayout.addWidget(self.kilroyProtocols.valveCommands.mainWidget, 1,0,1,1)
        self.mainLayout.addWidget(self.kilroyProtocols.pumpCommands.mainWidget, 1,1,1,1)

        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Valve Protocols")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

        # Define close menu item
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # Add menu items
        menubar = self.menuBar()
        for [menu_ID, menu_name] in enumerate(self.kilroyProtocols.menu_names):
            new_menu = menubar.addMenu("&" + menu_name)
            
            for menu_item in self.kilroyProtocols.menu_items[menu_ID]:
                new_menu.addAction(menu_item)

            # Add quit option to file menu
            if menu_name == "File":
                new_menu.addAction(self.exit_action)

    # ----------------------------------------------------------------------------------------
    # Handle close event
    # ----------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.kilroyProtocols.close()
        self.close()
  
# ----------------------------------------------------------------------------------------
# Test/Demo of Class
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

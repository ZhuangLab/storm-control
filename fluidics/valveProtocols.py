#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A class to load, parse, and control predefined valve protocols, i.e.
# collections of predefined valve commands and durations. This class also
# provides a basic I/O GUI to interface with protocols. 
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
from PyQt4 import QtCore, QtGui
from valveCommands import ValveCommands

# ----------------------------------------------------------------------------------------
# ValveProtocols Class Definition
# ----------------------------------------------------------------------------------------
class ValveProtocols(QtGui.QMainWindow):

    # Define custom command ready signal
    # --determines when a command is ready to be read
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
        
        # Create instance of ValveCommands class
        self.valveCommands = ValveCommands(xml_file_path = self.command_xml_path,
                                           verbose = self.verbose)

        # Connect valve command issue signal
        self.valveCommands.change_command_signal.connect(self.issueCommand)
        
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
    # Create display and control widgets
    # ------------------------------------------------------------------------------------                                                
    def createGUI(self):
        self.mainWidget = QtGui.QGroupBox()
        self.mainWidget.setTitle("Valve Protocols")
        self.mainWidgetLayout = QtGui.QVBoxLayout(self.mainWidget)

        self.fileLabel = QtGui.QLabel()
        self.fileLabel.setText("")

        self.protocolListWidget = QtGui.QListWidget()
        self.protocolListWidget.currentItemChanged.connect(self.updateProtocolDescriptor)

        self.elapsedTimeLabel = QtGui.QLabel()
        self.elapsedTimeLabel.setText("Elapsed Time: ")

        self.protocolDetailsList =  QtGui.QListWidget()
        
        self.startProtocolButton = QtGui.QPushButton("Start Protocol")
        self.startProtocolButton.clicked.connect(self.startProtocol)
        self.stopProtocolButton = QtGui.QPushButton("Stop Protocol")
        self.stopProtocolButton.clicked.connect(self.stopProtocol)
        
        self.protocolStatusGroupBox = QtGui.QGroupBox()
        self.protocolStatusGroupBox.setTitle("Command In Progress")
        self.protocolStatusGroupBoxLayout = QtGui.QVBoxLayout(self.protocolStatusGroupBox)
        
        self.mainWidgetLayout.addWidget(self.fileLabel)
        self.mainWidgetLayout.addWidget(self.protocolListWidget)
        self.mainWidgetLayout.addWidget(self.elapsedTimeLabel)
        self.mainWidgetLayout.addWidget(self.protocolDetailsList)
        self.mainWidgetLayout.addWidget(self.startProtocolButton)
        self.mainWidgetLayout.addWidget(self.stopProtocolButton)
        self.mainWidgetLayout.addStretch(1)
        
        # Menu items (may not be used)
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.closeEvent)

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
    # Return a protocol index by name
    # ------------------------------------------------------------------------------------                                        
    def getProtocolByName(self, command_name):
        try:
            command_ID = self.command_names.index(command_name)
            return self.commands[command_ID]
        except:
            print "Did not find " + command_name
            return [-1]*self.num_valves # Return no change command

    # ------------------------------------------------------------------------------------
    # Return loaded protocol names
    # ------------------------------------------------------------------------------------                                        
    def getProtocolNames(self):
        return self.protocol_names

    # ------------------------------------------------------------------------------------
    # Issue a command: load current command, send command ready signal
    # ------------------------------------------------------------------------------------                       
    def issueCommand(self, command_name, command_duration=-1):
        self.issued_command = self.valveCommands.getCommandByName(command_name)
        self.command_ready_signal.emit()
        if self.verbose:
            print "Issued: " + command_name + ": " + str(command_duration) + " s"
            print self.issued_command
        if command_duration >= 0:
            self.protocol_timer.start(command_duration*1000)

    # ------------------------------------------------------------------------------------
    # Load a protocol xml file
    # ------------------------------------------------------------------------------------                        
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

    # ------------------------------------------------------------------------------------
    # Parse loaded xml file: load protocols
    # ------------------------------------------------------------------------------------                                        
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

    # ------------------------------------------------------------------------------------
    # Display loaded protocols
    # ------------------------------------------------------------------------------------                                                
    def printProtocols(self):
        print "Current protocols:"
        for protocol_ID in range(self.num_protocols):
            print self.protocol_names[protocol_ID]
            for command_ID, command in enumerate(self.protocol_commands[protocol_ID]):
                textString = "    " + command + ": "
                textString += str(self.protocol_durations[protocol_ID][command_ID]) + " s"
                print textString

    # ------------------------------------------------------------------------------------
    # Initialize and start a protocol and issue first command
    # ------------------------------------------------------------------------------------
    def startProtocol(self):
        protocol_ID = self.protocolListWidget.currentRow()
        
        # Get first command in protocol
        command_name = self.protocol_commands[protocol_ID][0]
        command_duration = self.protocol_durations[protocol_ID][0]

        # Set protocol status: [protocol_ID, command_ID]
        self.status = [protocol_ID, 0]

        if self.verbose:
            print "Starting " + self.protocol_names[protocol_ID]

        # Issue command signal
        self.issueCommand(command_name, command_duration)

        # Start elapsed time timer
        self.elapsed_timer.start()
        self.poll_elapsed_time_timer.start()

        # Change enable status of GUI items
        self.startProtocolButton.setEnabled(False)
        self.protocolListWidget.setEnabled(False)
        self.protocolDetailsList.setCurrentRow(0)

        ### ADD CODE TO DISABLE WIDGETS FROM OTHER CLASSES
    
    # ------------------------------------------------------------------------------------
    # Stop a running protocol either on completion or early
    # ------------------------------------------------------------------------------------               
    def stopProtocol(self):
        self.status = [-1,-1]
        self.protocol_timer.stop()
        if self.verbose:
            print "Stopped Protocol"

        self.startProtocolButton.setEnabled(True)
        self.protocolListWidget.setEnabled(True)
        
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

        self.fileLabel.setText(self.protocol_xml_path)

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
            text_string = current_protocol_commands[ID]
            text_string += ": "
            text_string += str(current_protocol_durations[ID]) + " s"

            wid = QtGui.QListWidgetItem(text_string)
            wid.setFlags(wid.flags() & QtCore.Qt.ItemIsSelectable)
            self.protocolDetailsList.insertItem(ID, wid)

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------                                                                
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.valveProtocols = ValveProtocols(verbose = True)
                                  
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.mainLayout.addWidget(self.valveProtocols.mainWidget)
        self.mainLayout.addWidget(self.valveProtocols.valveCommands.mainWidget)

        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("Valve Protocols")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

# ----------------------------------------------------------------------------------------
# Test/Demo of Class
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

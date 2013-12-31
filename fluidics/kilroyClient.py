#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A TCP communication class that acts as the client side for the kilroy TCP server
# This class can be incorporated into programs to allow them to remotely call
# kilroy protocols
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/28/13
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import time
from PyQt4 import QtCore, QtGui, QtNetwork

# ----------------------------------------------------------------------------------------
# Kilroy Socket Class: Based on Hazen's HALSocket
# ----------------------------------------------------------------------------------------
class KilroySocket(QtNetwork.QTcpSocket):

    # Define custom command ready signal
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(str)
    
    def __init__(self,
                 parent = None,
                 port=9500,
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 verbose = False):
        QtNetwork.QTcpSocket.__init__(self, parent)

        # Initialize internal variables
        self.verbose = verbose
        self.address = address # Default is local address
        self.port = port # Default is port 9500 
        self.is_connected = False

         # Define custom response strings
        self.acknowledge = "Ack"
        self.already_connected = "Busy"
        self.command_complete = "Complete"
        self.no_command = "NA"
        self.new_line = "\n"
        self.delimiter = ","
        
        # Connect data ready signal
        self.readyRead.connect(self.handleReadyRead)

    # ------------------------------------------------------------------------------------
    # Close 
    # ------------------------------------------------------------------------------------       
    def close(self):
        if self.verbose: print "Closing kilroy socket"

    # ------------------------------------------------------------------------------------
    # Connect to Kilroy Server 
    # ------------------------------------------------------------------------------------       
    def connectToServer(self):
        if self.verbose:
            string = "Looking for kilroy server at: \n"
            string += "    Address: " + self.address.toString() + "\n"
            string += "    Port: " + str(self.port)
            print string

        self.connectToHost(self.address, self.port)
        tries = 0
        while (not self.waitForConnected() and (tries < 5)):
            print "Could not find Kilroy server. Attempt: " + str(tries)
            time.sleep(1)
            self.connectToHost(self.address, self.port)
            tries += 1
            
        if tries==5:
            print "No Kilroy server found"
        else:
            print "Connected to Kilroy"

    # ------------------------------------------------------------------------------------
    # Handle new data triggered by the readyRead signal 
    # ------------------------------------------------------------------------------------       
    def handleReadyRead(self):
        while self.canReadLine():
            line = str(self.readLine()).strip()
            parsed_line = line.split(',') # Split on delimiter
            if len(parsed_line) == 1: #Signal command 
                if (parsed_line[0] == self.acknowledge): # Acknowledgement
                    self.acknowledged.emit()
                elif parsed_line[0] == self.already_connected: # Busy signal
                    self.socket.disconnectFromHost()
            elif len(parsed_line) > 1: # Composite command
                if parsed_line[0] == self.command_complete:
                    self.complete.emit(parsed_line[1])

    # ------------------------------------------------------------------------------------
    # Send command 
    # ------------------------------------------------------------------------------------       
    def sendCommand(self, command):
        if self.verbose:
            print "Kilroy Socket: Sending: " + command
        self.write(str(command + "\n"))

        #####self.flush() #Is this needed?

        
# ----------------------------------------------------------------------------------------
# Kilroy Client Class
# ----------------------------------------------------------------------------------------                                                                
class KilroyClient(QtGui.QWidget):
    # Define custom command ready signal: to relay Socket Signals to Owning Class
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(str)
    disconnect = QtCore.pyqtSignal()

    def __init__(self,
                 parent = None,
                 port=9500,
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 verbose = False):
        QtGui.QWidget.__init__(self, parent)

        # Define attributes
        self.address = address # Default is local machine
        self.port = port # Default is 9500
        self.verbose = verbose
        self.unacknowledged_messages = 0
        self.command_pause_time = 0.05
        self.kilroy_state = None # Keep track of what kilroy is doing
        self.protocol_header = "Protocol,"
        
        # Create instance of KilroySocket
        self.socket = KilroySocket(port = self.port,
                                   verbose = self.verbose)
        
        # Connect KilroySocket signals
        self.socket.acknowledged.connect(self.handleAcknowledged)
        self.socket.complete.connect(self.handleComplete)
        self.socket.disconnected.connect(self.handleDisconnect)

        # Create GUI
        self.createGUI()
        self.updateGUI()

    # ------------------------------------------------------------------------------------
    # Close 
    # ------------------------------------------------------------------------------------       
    def close(self):
        if self.verbose: print "Closing kilroy client"
        if self.isConnected(): self.socket.close()
        
    # ------------------------------------------------------------------------------------
    # Create GUI 
    # ------------------------------------------------------------------------------------       
    def createGUI(self):
        self.mainWidget = QtGui.QGroupBox()
        self.mainWidget.setTitle("Kilroy Client")
        self.mainWidgetLayout = QtGui.QVBoxLayout(self.mainWidget) 

        self.addressLabel = QtGui.QLabel()

        self.portLabel = QtGui.QLabel()
        
        self.isSocketConnected = QtGui.QLabel()

        self.protocolToSendLabel = QtGui.QLabel()
        self.protocolToSendLabel.setText("Protocol Name:")

        self.protocolToSend = QtGui.QLineEdit()

        self.sendProtocolButton = QtGui.QPushButton("Send Protocol Command")
        self.sendProtocolButton.clicked.connect(self.handleSendProtocolButton)
        
        self.mainWidgetLayout.addWidget(self.addressLabel)
        self.mainWidgetLayout.addWidget(self.portLabel)
        self.mainWidgetLayout.addWidget(self.isSocketConnected)
        self.mainWidgetLayout.addWidget(self.protocolToSendLabel)
        self.mainWidgetLayout.addWidget(self.protocolToSend)
        self.mainWidgetLayout.addWidget(self.sendProtocolButton)
        
        self.mainWidgetLayout.addStretch(1)

        # Configure menu items 
        self.menu_names = ["File"]
        self.menu_items = [[ ]]

    # ------------------------------------------------------------------------------------
    # Update GUI based on protocols
    # ------------------------------------------------------------------------------------                                                
    def updateGUI(self):
        self.addressLabel.setText("Address: " + self.address.toString())
        self.portLabel.setText("Port: " + str(self.port))

        num_clients = 0
        if self.isConnected():
            self.isSocketConnected.setText("Connection Status: Server Found")
        else:
            self.isSocketConnected.setText("Connection Status: No Server Found")
        
    # ------------------------------------------------------------------------------------
    # Handle acknowledged receipt of transmitted message 
    # ------------------------------------------------------------------------------------       
    def handleAcknowledged(self):
        self.unacknowledged_messages -= 1
        if self.unacknowledged_messages == 0:
            self.acknowledged.emit() # All messages have been sent and received
        
    # ------------------------------------------------------------------------------------
    # Handle completion of signal command 
    # ------------------------------------------------------------------------------------       
    def handleComplete(self, command_string):
        if self.kilroy_state == "Running Protocol":
            print "Completed Protocol: " + command_string
        else:
            print "Completed unknown function: " + command_string

        self.complete.emit(command_string)
        self.kilroy_state = None

    # ------------------------------------------------------------------------------------
    # Pass server disconnect signal 
    # ------------------------------------------------------------------------------------       
    def handleDisconnect(self):
        self.disconnect.emit()

    # ------------------------------------------------------------------------------------
    # Return true if socket exists and is connected 
    # ------------------------------------------------------------------------------------       
    def isConnected(self):
        if (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False   

    # ------------------------------------------------------------------------------------
    # Send a command to Kilroy via the Kilroy Socket 
    # ------------------------------------------------------------------------------------       
    def sendCommand(self, command):
        if self.isConnected():
            self.unacknowledged_messages += 1
            self.socket.sendCommand(command)
            self.socket.flush()
            time.sleep(self.command_pause_time)
            return True
        else:
            print "Kilroy socket not connected. Did not send: " + command
            return False      

    # ------------------------------------------------------------------------------------
    # Send protocol command to Kilroy 
    # ------------------------------------------------------------------------------------       
    def sendProtocol(self, protocol_name):
        if self.verbose:
            print "Sending protocol request: " + protocol_name
        was_command_sent = self.sendCommand(self.protocol_header + protocol_name)
        if was_command_sent:
            self.kilroy_state = "Running Protocol"

    # ------------------------------------------------------------------------------------
    # Send protocol command to Kilroy via GUI (Testing purposes only)
    # ------------------------------------------------------------------------------------       
    def handleSendProtocolButton(self):
        protocol_name = self.protocolToSend.displayText()

        self.sendProtocol(protocol_name)

        self.protocolToSend.clear()

    # ------------------------------------------------------------------------------------
    # Disconnect the Kilroy socket from the host
    # ------------------------------------------------------------------------------------       
    def stopCommunication(self):
        if self.isConnected():
            self.socket.disconnectFromHost()
            if self.verbose:
                print "Disconnected Kilroy Client from Kilroy Server"

    # ------------------------------------------------------------------------------------
    # Attempt to connect socket
    # ------------------------------------------------------------------------------------       
    def startCommunication(self):
        if not self.isConnected():
            self.socket.connectToServer()
            self.unacknowledged_messages = 0
    
# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------                                                                
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.tcpClient = KilroyClient(port = 9500,
                                      verbose = True)
                                  
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.mainLayout.addWidget(self.tcpClient.mainWidget)

        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("TCP Client")

        # set window geometry
        self.setGeometry(50, 50, 500, 200)

        # Define close menu item
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # Add menu items
        menubar = self.menuBar()
        for [menu_ID, menu_name] in enumerate(self.tcpClient.menu_names):
            new_menu = menubar.addMenu("&" + menu_name)
            
            for menu_item in self.tcpClient.menu_items[menu_ID]:
                new_menu.addAction(menu_item)

            # Add quit option to file menu
            if menu_name == "File":
                new_menu.addAction(self.exit_action)

        # Open the Kilroy Socket and Connect to Server
        self.tcpClient.startCommunication()
    # ----------------------------------------------------------------------------------------
    # Handle close event
    # ----------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.tcpClient.close()
        self.close()
        
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

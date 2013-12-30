#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A TCP/IP communication class that can be incorporated into Kilroy
#   Based on tcpClient from HAL-4000 by Hazen Babcock
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 12/28/13
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
from PyQt4 import QtCore, QtGui, QtNetwork

# ----------------------------------------------------------------------------------------
# ValveProtocols Class Definition
# ----------------------------------------------------------------------------------------
class TCPLocalServer(QtNetwork.QTcpServer):

    # Define custom command ready signal
    com_got_connection = QtCore.pyqtSignal()
    com_lost_connection = QtCore.pyqtSignal()
    data_ready = QtCore.pyqtSignal() # Data added to buffer

    def __init__(self, port, parent = None, verbose = False):
        QtNetwork.QTcpServer.__init__(self, parent)

        # Initialize internal variables
        self.verbose = verbose
        self.address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost);
        self.port = port
        self.socket = None
        self.data_buffer = []
        self.num_data = 0
        self.last_command_written = []

        # Define custom response strings
        self.acknowledge = QtCore.QByteArray("Ack")
        self.command_complete = QtCore.QByteArray("Complete,")
        self.new_line = QtCore.QByteArray("\n")
        
        # Connect new connection signal
        self.newConnection.connect(self.handleClientConnection)

        # Create GUI
        self.createGUI()
        self.updateGUI()
        
        # Listen for new connections
        self.connectToNewClients()

    # ------------------------------------------------------------------------------------
    # Create GUI elements 
    # ------------------------------------------------------------------------------------       
    def createGUI(self):
        self.mainWidget = QtGui.QGroupBox()
        self.mainWidget.setTitle("TCP Server")
        self.mainWidgetLayout = QtGui.QVBoxLayout(self.mainWidget) 

        self.addressLabel = QtGui.QLabel()

        self.portLabel = QtGui.QLabel()
        
        self.isPortConnected = QtGui.QLabel()

        self.writtenData = QtGui.QLabel()
        self.writtenData.setText("Written Data: ")

        self.dataBufferLabel = QtGui.QLabel()
        self.dataBufferLabel.setText("Data Buffer")

        self.dataBuffer = QtGui.QListWidget()
        
        self.mainWidgetLayout.addWidget(self.addressLabel)
        self.mainWidgetLayout.addWidget(self.portLabel)
        self.mainWidgetLayout.addWidget(self.isPortConnected)
        self.mainWidgetLayout.addWidget(self.writtenData)
        self.mainWidgetLayout.addWidget(self.dataBufferLabel)
        self.mainWidgetLayout.addWidget(self.dataBuffer)
        
        self.mainWidgetLayout.addStretch(1)

        # Configure menu items 
        self.menu_names = ["File"]
        self.menu_items = [[ ]]

    # ------------------------------------------------------------------------------------
    # Listen for new clients 
    # ------------------------------------------------------------------------------------       
    def connectToNewClients(self):
        if self.verbose: print "Listening for new clients"
        self.listen(self.address, self.port)
        if self.verbose: print "Found client"
        self.com_got_connection.emit()
        
    # ------------------------------------------------------------------------------------
    # Disconnect from all clients 
    # ------------------------------------------------------------------------------------       
    def disconnectFromClients(self):
        if self.verbose:
            print "Force disconnect from clients"
        if self.isConnected():
            self.socket.disconnectFromHost()
            self.socket.waitForDisconnect()
            self.socket.close()
            self.socket = None
            self.com_lost_connection.emit()
            self.connectToNewClients()

    # ------------------------------------------------------------------------------------
    # Remove data from buffer 
    # ------------------------------------------------------------------------------------       
    def getLastDataElement(self):
        if self.num_data > 0:
            data_packet = self.data_buffer.pop()
            self.num_data -= 1
        else:
            data_packet = None

        if self.verbose:
            print "Returning: " + data_packet

        return data_packet

    # ------------------------------------------------------------------------------------
    # Handle connection of a new client 
    # ------------------------------------------------------------------------------------       
    def handleClientConnection(self):
        socket = self.nextPendingConnection()

        if not self.isConnected():
            self.socket = socket
            self.socket.readyRead.connect(self.handleNewData)
            self.socket.disconnected.connect(self.handleClientDisconnect)
            self.com_got_connection.emit()
            if self.verbose:
                print "Connected new client"
    
    # ------------------------------------------------------------------------------------
    # Handle client disconnect 
    # ------------------------------------------------------------------------------------       
    def handleClientDisconnect(self):
        self.socket.disconnectFromHost()
        self.socket.close()
        self.socket = None
        self.com_lost_connection.emit()
        if self.verbose:
            print "Client disconnected"
    
    # ------------------------------------------------------------------------------------
    # Handle client disconnect 
    # ------------------------------------------------------------------------------------       
    def handleNewData(self):
        while self.socket.canReadLine():
            # Read data line
            data = str(self.socket.readLine())[:-1]

            # Store data line
            self.data_buffer.append(data)
            self.num_data += 1

            # Emit data ready signal
            self.data_ready.emit()

            # Display data
            if self.verbose:
                print "Received: " + data
            
            # Acknowledge data 
            self.socket.write(self.acknowledge + self.new_line)
            self.socket.flush()
            self.last_command_written = self.acknowledge 

        self.updateGUI()

    # ------------------------------------------------------------------------------------
    # Return true if connected 
    # ------------------------------------------------------------------------------------       
    def isConnected(self):
        if self.socket and (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False
        
    # ------------------------------------------------------------------------------------
    # Handle client disconnect 
    # ------------------------------------------------------------------------------------       
    def sendCompleteCommand(self, command_str):
        if self.isConnected():
            command_to_send = self.command_complete + command_str
            self.socket.write(command_to_send + self.new_line)
            self.socket.flush()
            self.last_command_written = command_to_send

            self.updateGUI()

    # ------------------------------------------------------------------------------------
    # Update GUI based on protocols
    # ------------------------------------------------------------------------------------                                                
    def updateGUI(self):
        self.addressLabel.setText("Address: " + self.address.toString())
        self.portLabel.setText("Port: " + str(self.port))

        num_clients = 0
        if self.isConnected():
            num_clients += 1
        self.isPortConnected.setText("Clients: " + str(num_clients))

        self.dataBuffer.clear()
        for data in self.data_buffer:
            self.dataBuffer.addItem(data)

# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------                                                                
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # scroll area widget contents - layout
        self.tcpServer = TCPLocalServer(port = 9000,
                                        verbose = True)
                                  
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.mainLayout.addWidget(self.tcpServer.mainWidget)

        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        # set window title
        self.setWindowTitle("TCP Server")

        # set window geometry
        self.setGeometry(50, 50, 500, 400)

        # Define close menu item
        self.exit_action = QtGui.QAction("Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # Add menu items
        menubar = self.menuBar()
        for [menu_ID, menu_name] in enumerate(self.tcpServer.menu_names):
            new_menu = menubar.addMenu("&" + menu_name)
            
            for menu_item in self.tcpServer.menu_items[menu_ID]:
                new_menu.addAction(menu_item)

            # Add quit option to file menu
            if menu_name == "File":
                new_menu.addAction(self.exit_action)
            
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

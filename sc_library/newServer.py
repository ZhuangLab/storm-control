#!/usr/bin/python
# ----------------------------------------------------------------------------------------
# A TCP communication class that acts as the server side for generic communications
# between programs in the storm-control project
# ----------------------------------------------------------------------------------------
# Jeff Moffitt
# 3/8/14
# jeffmoffitt@gmail.com
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Import
# ----------------------------------------------------------------------------------------
import sys
import time
import pickle
from PyQt4 import QtCore, QtGui, QtNetwork
from sc_library.tcpMessage import TCPMessage

# ----------------------------------------------------------------------------------------
# Server Class 
# ----------------------------------------------------------------------------------------
class TCPServer(QtNetwork.QTcpServer):

    # Define custom command ready signal
    com_got_connection = QtCore.pyqtSignal()
    com_lost_connection = QtCore.pyqtSignal()
    message_ready = QtCore.pyqtSignal()

    def __init__(self,
                 port=9500,
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 parent = None,
                 verbose = False):
        QtNetwork.QTcpServer.__init__(self, parent)

        # Initialize internal variables
        self.verbose = verbose
        self.address = address; # Default is local address
        self.port = port # 9500 is default Kilroy port
        self.socket = None
        self.message_buffer = []
        self.num_message = 0
        self.last_message_written = []    
        
        # Connect new connection signal
        self.newConnection.connect(self.handleClientConnection)
        
        # Listen for new connections
        self.connectToNewClients()

    # ------------------------------------------------------------------------------------
    # Close 
    # ------------------------------------------------------------------------------------       
    def close(self):
        if self.verbose: print "Closing TCP server"
        if self.socket: self.socket.close()

    # ------------------------------------------------------------------------------------
    # Listen for new clients 
    # ------------------------------------------------------------------------------------       
    def connectToNewClients(self):
        if self.verbose:
            string = "Listening for new clients at: \n"
            string += "    Address: " + self.address.toString() + "\n"
            string += "    Port: " + str(self.port)
            print string
        self.listen(self.address, self.port)
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
    # Remove message from Buffer 
    # ------------------------------------------------------------------------------------       
    def getLastMessage(self):
        if self.num_message > 0:
            message = self.message_buffer.pop()
            self.num_message -= 1
        else:
            message = None
        
        return message

    # ------------------------------------------------------------------------------------
    # Parse data in buffer into protocol name 
    # ------------------------------------------------------------------------------------       
    def getMessage(self):
        return self.getLastMessage()

    # ------------------------------------------------------------------------------------
    # Handle connection of a new client 
    # ------------------------------------------------------------------------------------       
    def handleClientConnection(self):
        socket = self.nextPendingConnection()

        if not self.isConnected():
            self.socket = socket
            self.socket.readyRead.connect(self.handleNewMessage)
            self.socket.disconnected.connect(self.handleClientDisconnect)
            self.com_got_connection.emit()
            if self.verbose:
                print "Connected new client"
        else: # Refuse new socket if one already exists
            message = TCPMessage(message_type = "Busy")
            socket.write(pickle.dumps(message))
            socket.disconnectFromHost()
            socket.close()
        
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
    # Handles a new message on the socket (receives the readyRead signal from the socket)
    # ------------------------------------------------------------------------------------       
    def handleNewMessage(self):
        message_str = ""
        while self.socket.canReadLine():
            # Read data line
            message_str += str(self.socket.readLine())
        message = pickle.loads(message_str)
        
        # Store message
        self.message_buffer.append(message)
        self.num_message += 1
        
        # Acknowledge data
        ack_message = TCPMessage(message_type = "Acknowledge")
        ack_string = pickle.dumps(ack_message)
        self.send(ack_string)

        # Emit data ready signal
        self.message_ready.emit()

    # ------------------------------------------------------------------------------------
    # Return true if connected 
    # ------------------------------------------------------------------------------------       
    def isConnected(self):
        if self.socket and (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False

    # ------------------------------------------------------------------------------------
    # Send message
    # ------------------------------------------------------------------------------------       
    def send(self, message_str):
        if self.isConnected():
            self.socket.write(message_str + "\n")
            self.socket.flush()
        
# ----------------------------------------------------------------------------------------
# Stand Alone Test Class
# ----------------------------------------------------------------------------------------                                                                
class StandAlone(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # Create server
        self.server = TCPServer(port = 9500, verbose = True)

        # Connect PyQt signals
        self.server.com_got_connection.connect(self.handleNewConnection)
        self.server.com_lost_connection.connect(self.handleLostConnection)
        self.server.message_ready.connect(self.handleMessageReady)            

    # ----------------------------------------------------------------------------------------
    # Handle New Connection
    # ----------------------------------------------------------------------------------------
    def handleNewConnection(self):
        print "Established connection"

    # ----------------------------------------------------------------------------------------
    # Handle Lost Connection
    # ----------------------------------------------------------------------------------------
    def handleLostConnection(self):
        print "Lost connection"

    # ----------------------------------------------------------------------------------------
    # Handle New Message
    # ----------------------------------------------------------------------------------------
    def handleMessageReady(self):
        message = self.server.getMessage()
        print "Received: ", message
        
    # ----------------------------------------------------------------------------------------
    # Handle close event
    # ----------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.server.close()
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

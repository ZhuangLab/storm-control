#!/usr/bin/python
# 
# A TCP communication class that acts as the server side for generic communications
# between programs in the storm-control project
# 
# Jeff Moffitt
# 3/8/14
# jeffmoffitt@gmail.com
#

import sys
import pickle
from PyQt4 import QtCore, QtGui, QtNetwork
from sc_library.tcpMessage import TCPMessage
import sc_library.tcpCommunications as tcpCommunications

## TCPServer
#
# A TCP server for passing TCP messages between programs
#
class TCPServer(QtNetwork.QTcpServer, tcpCommunications.TCPCommunications):
    messageReceived = tcpCommunications.TCPCommunications.messageReceived
    comGotConnection = QtCore.pyqtSignal()
    comLostConnection = QtCore.pyqtSignal()
    
    ## __init__
    #
    # Class constructor
    #
    # @param parent A reference to an owning class.
    # @param port The TCP/IP port for communication.
    # @param server_name A string name for the communication server.
    # @param address An address for the TCP/IP communication.
    # @param verbose A boolean controlling the verbosity of the class
    #
    def __init__(self,
                 port = 9500,
                 server_name = "default",
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 parent = None,
                 verbose = False):
        QtNetwork.QTcpServer.__init__(self, parent)
        tcpCommunications.TCPCommunications.__init__(self,
                                                     parent=parent,
                                                     port=port,
                                                     server_name=server_name,
                                                     address=address,
                                                     verbose=verbose)

        # Connect new connection signal
        self.newConnection.connect(self.handleClientConnection)
        
        # Listen for new connections
        self.connectToNewClients()

    ## connectToNewClients
    #
    # Listen for new clients
    #
    def connectToNewClients(self):
        if self.verbose:
            string = "Listening for new clients at: \n"
            string += "    Address: " + self.address.toString() + "\n"
            string += "    Port: " + str(self.port)
            print string
        self.listen(self.address, self.port)
        self.comGotConnection.emit()
        
    ## disconnectFromClients
    #
    # Disconnect from clients
    #
    def disconnectFromClients(self):
        if self.verbose:
            print "Force disconnect from clients"
        if self.isConnected():
            self.socket.disconnectFromHost()
            self.socket.waitForDisconnect()
            self.socket.close()
            self.socket = None
            self.comLostConnection.emit()
            self.connectToNewClients()
    
    ## handleClientConnection
    #
    # Handle connection from a new client
    #
    def handleClientConnection(self):
        socket = self.nextPendingConnection()

        if not self.isConnected():
            self.socket = socket
            self.socket.readyRead.connect(self.handleReadyRead)
            self.socket.disconnected.connect(self.handleClientDisconnect)
            self.comGotConnection.emit()
            if self.verbose: print "Connected new client"
        else: # Refuse new socket if one already exists
            message = TCPMessage(message_type = "Busy") # from tcpMessage.TCPMessage
            if self.verbose: print "Sent: \n" + str(message)
            socket.write(pickle.dumps(message) + "\n")
            socket.disconnectFromHost()
            socket.close()
        
    ## handleClientDisconnect
    #
    # Handle diconnection of client
    #
    def handleClientDisconnect(self):
        self.socket.disconnectFromHost()
        self.socket.close()
        self.socket = None
        self.comLostConnection.emit()
        if self.verbose: print "Client disconnected"
        
## StandAlone
# 
# Stand Alone Test Class
#                                                               
class StandAlone(QtGui.QMainWindow):

    ## __init__
    #
    # @param parent (optional) The PyQt parent of this object, defaults to none.
    #
    def __init__(self, parent = None):
        super(StandAlone, self).__init__(parent)

        # Create server
        self.server = TCPServer(port = 9500, verbose = True)

        # Connect PyQt signals
        self.server.comGotConnection.connect(self.handleNewConnection)
        self.server.comLostConnection.connect(self.handleLostConnection)
        self.server.messageReady.connect(self.handleMessageReady)            

    ## handleNewConnection
    # 
    # Handle New Connection.
    # 
    def handleNewConnection(self):
        print "Established connection"

    ## handleLostConnection
    # 
    # Handle Lost Connection.
    # 
    def handleLostConnection(self):
        print "Lost connection"

    ## handleMessageReady
    # 
    # Handle New Message.
    #
    # @param message A TCPMessage object.
    # 
    def handleMessageReady(self, message):
        # Parse Based on Message Type
        if message.getType() == "Stage Position":
            print "Stage X: ", message.getData("Stage_X"), "Stage Y: ", message.getData("Stage_Y")
            self.server.sendMessage(message)
            
        elif message.getType() == "Movie":
            print "Movie: ", "Name: ", message.getData("Name"), "Parameters: ", message.getData("Parameters")
            self.server.sendMessage(message)

    ## closeEvent
    # 
    # Handle close event.
    #
    # @param event A PyQt QEvent object.
    # 
    def closeEvent(self, event):
        self.server.close()
        self.close()
            
# 
# Test/Demo of Class
#                        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = StandAlone()
    window.show()
    sys.exit(app.exec_())

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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

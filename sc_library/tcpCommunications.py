#!/usr/bin/python
#
## @file 
#
# A TCP communications class that provides the basic methods for relaying TCP messages.
#
# Jeffrey Moffitt
# 3/16/14
# jeffmoffitt@gmail.com
#
# Hazen 05/14
#

from PyQt4 import QtCore, QtNetwork
from sc_library.tcpMessage import TCPMessage

## TCPCommunications
#
# An abstract class used to define the basic process of exchanging TCP messages. Client and
# servers should be inherited from this class.
#
class TCPCommunications(QtCore.QObject):
    messageReceived = QtCore.pyqtSignal(object) # Relay received TCP messages.

    ## __init__
    #
    # Constructor for this class.
    #
    # @param parent A reference to an owning class.
    # @param port The TCP/IP port for communication.
    # @param server_name A string name for the communication server.
    # @param address An address for the TCP/IP communication. Defaults to the local machine.
    # @param verbose A boolean controlling the verbosity of the class.
    #
    def __init__(self,
                 port=9500,
                 server_name = "default",
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 parent = None,
                 verbose = False):
        QtCore.QObject.__init__(self)
        
        # Initialize internal attributes
        self.address = address
        self.port = port 
        self.server_name = server_name
        self.socket = None
        self.verbose = verbose
    
    ## close
    #
    # Close the socket
    #
    def close(self):
        if self.socket:
            self.socket.close()
            if self.verbose: print "Closing TCP communications: " + self.server_name
            
    ## handleBusy
    #
    # Handle a busy message. Reserved for future use.
    #
    def handleBusy(self):
        pass

    ## handleReadyRead
    #
    # Create TCP message class from JSON message and forward as appropriate
    #
    def handleReadyRead(self):
        message_str = ""
        while self.socket.canReadLine():
            # Read data line
            message_str += str(self.socket.readLine())

        # Create message.
        message = TCPMessage.fromJSON(message_str)
        if self.verbose: print "Received: \n" + str(message)

        if message.getType() == "Busy":
            self.handleBusy()
        else:
            self.messageReceived.emit(message)
    
    ## isConnected
    #
    # Return true if the socket is connected and active.
    #
    # @return A boolean describing the connected state of the socket.
    #
    def isConnected(self):
        if self.socket and (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False

    ## sendMessage
    #
    # Send TCP message as JSON string if the socket is connected.
    #
    # @param message A TCPMessage object.
    #
    def sendMessage(self, message):
        if self.isConnected():
            #message_str = pickle.dumps(message)
            self.socket.write(message.toJSON() + "\n")
            self.socket.flush()
            if self.verbose: print "Sent: \n" + str(message)
        else:
            print self.server_name + " socket not connected. \nDid not send:" 
            message.setError(True, "Communication Error: " + self.server_name + " socket not connected")
            print message
            self.messageReceived.emit(message) # Return message with error

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


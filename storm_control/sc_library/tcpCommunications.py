#!/usr/bin/env python
"""
A TCP communications class that provides the basic methods for relaying TCP messages.

Jeffrey Moffitt
3/16/14
jeffmoffitt@gmail.com

Hazen 05/14
"""

from PyQt5 import QtCore, QtNetwork

from storm_control.sc_library.tcpMessage import TCPMessage


class TCPCommunicationsMixin(object):
    """
    A mixin class that defines the basic process of exchanging TCP 
    messages. Client and servers (multi-) inherit this class.

    They will should also include the following signal:
    messageReceived = QtCore.pyqtSignal(object)
    """
    def __init__(self,
                 address = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost),
                 encoding = 'utf-8',
                 port = 9500,
                 server_name = "default",
                 verbose = False,
                 **kwds):
        super().__init__(**kwds)

        # Initialize internal attributes
        self.address = address
        self.encoding = encoding
        self.port = port 
        self.server_name = server_name
        self.socket = None
        self.verbose = verbose
    
    def close(self):
        """
        Close the socket.
        """
        if self.socket:
            self.socket.close()
            if self.verbose:
                print("Closing TCP communications: " + self.server_name)
            
    def handleBusy(self):
        """
        Handle a busy message. Reserved for future use.
        """
        pass

    def handleReadyRead(self):
        """
        Create TCP message class from JSON message and forward as appropriate
        """
        message_str = ""
        while self.socket.canReadLine():
            # Read data line
            message_str += str(self.socket.readLine(), self.encoding)

        # Create message.
        message = TCPMessage.fromJSON(message_str)
        if self.verbose:
            print("Received: \n" + str(message))

        if (message.getType() == "Busy"):
            self.handleBusy()
        else:
            self.messageReceived.emit(message)
    
    def isConnected(self):
        """
        Return true if the socket is connected and active.
        """
        if self.socket and (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False

    def sendMessage(self, message):
        """
        Send TCP message as JSON string if the socket is connected.
        """
        if self.isConnected():
            message_str = message.toJSON() + "\n"
            self.socket.write(message_str.encode(self.encoding))
            self.socket.flush()
            if self.verbose:
                print("Sent: \n" + str(message))
        else:
            print(self.server_name + " socket not connected. \nDid not send:" )
            message.setError(True, "Communication Error: " + self.server_name + " socket not connected")
            print(message)
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


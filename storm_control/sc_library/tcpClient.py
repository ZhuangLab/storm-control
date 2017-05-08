#!/usr/bin/env python
"""
A TCP communication class that acts as the client side for generic communications
between programs in the storm-control project

Jeffrey Moffitt
3/8/14
jeffmoffitt@gmail.com
"""

# 
# Import
# 
import sys
import time
from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets

from storm_control.sc_library.tcpMessage import TCPMessage
import storm_control.sc_library.tcpCommunications as tcpCommunications


class TCPClient(QtCore.QObject, tcpCommunications.TCPCommunicationsMixin):
    """
    A TCP client class used to transfer TCP messages from one program to another
    """
    comLostConnection = QtCore.pyqtSignal()
    messageReceived = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        # Create instance of TCP socket
        self.socket = QtNetwork.QTcpSocket()
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.readyRead.connect(self.handleReadyRead)

    def connectToServer(self):
        """
        Attempt to establish a connection with the server at the indicated address and port
        """
        if self.verbose:
            print("-"*50)
            string = "Looking for " + self.server_name + " server at: \n"
            string += "    Address: " + self.address.toString() + "\n"
            string += "    Port: " + str(self.port)
            print(string)

        # Attempt to connect to host.
        self.socket.connectToHost(self.address, self.port)

        if not self.socket.waitForConnected(1000):
            print(self.server_name + " server not found")

    def handleDisconnect(self):
        """
        Handles the disconnect from the socket.
        """
        self.comLostConnection.emit()

    def startCommunication(self):
        """
        Start communications with server
        """
        if not self.isConnected():
            self.connectToServer()
        return self.isConnected()

    def stopCommunication(self):
        """
        Stop communications with server.
        """
        if self.isConnected():
            self.socket.disconnectFromHost()


class StandAlone(QtWidgets.QMainWindow):
    """
    Stand Alone Test Class.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

        # Create client
        self.client = TCPClient(port = 9500, server_name = "Test", verbose = True)

        self.client.messageReceived.connect(self.handleMessageReceived)
        self.client.startCommunication()

        self.message_ID = 1
        self.sendTestMessage()

    def sendTestMessage(self):
        """
        Send test messages.
        """
        if (self.message_ID == 1):
            # Create Test message
            message = TCPMessage(message_type = "Stage Position",
                                 message_data = {"Stage_X": 100.00, "Stage_Y": 0.00})
        elif (self.message_ID ==2):
            message = TCPMessage(message_type = "Movie",
                                 message_data = {"Name": "Test_Movie_01", "Parameters": 1})

        else:
            message = TCPMessage(message_type = "Done")
    
        self.message_ID += 1
        self.sent_message = message
        self.client.sendMessage(message)
        
    def handleMessageReceived(self, message):
        """
        Handle new message.
        """
        # Handle responses to messages
        if (self.sent_message.getID() == message.getID()):
            print(message)
        else:
            print("Received an unexpected message")

        self.sendTestMessage()

    def closeEvent(self, event):
        """
        Handle close event.
        """
        self.client.close()
        self.close()


# 
# Test/Demo of Class
#                         
if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
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

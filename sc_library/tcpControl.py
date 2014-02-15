#!/usr/bin/python
#
## @file 
#
# Handles remote control (via TCP/IP of the data collection program)
#
# Hazen 02/14
#

import sys
from PyQt4 import QtCore, QtNetwork

import sc_library.hdebug as hdebug

## match
#
# Returns true if string2 is equal or longer than string1 and if 
# the strings match where they overlap.
#
# @param string1 The first string.
# @param string2 The second string.
#
def match(string1, string2):
    if len(string2) >= len(string1):
        if string1 == string2[0:len(string1)]:
            return True
        else:
            return False
    else:
        return False


## TCPMessage
#
# Contains the contents of a TCP command.
#
class TCPMessage():

    ## __init__
    #
    # @param command_type The type of the command.
    # @param command_data The data in the command.
    #
    def __init__(self, command_type, command_data):
        self.command_data = command_data
        self.command_type = command_type

    ## getType
    #
    # @return The command type.
    #
    def getType(self):
        return self.command_type

    ## getData
    #
    # @return The command data (as a list of values).
    #
    def getData(self):
        return self.command_data


## TCP/IP Control Class
#
# To allow only one connection at a time from the local computer
# the server is closed once the connection is made. When the
# connection is broken the server is opened again.
#
class TCPControl(QtNetwork.QTcpServer):
    commGotConnection = QtCore.pyqtSignal()
    commLostConnection = QtCore.pyqtSignal()
    commMessage = QtCore.pyqtSignal(object)

    ## __init__
    #
    # Create the TCPControl object, listening on the port specified by 
    # port. This is supposed to only accept connections from processes
    # on the same computer.
    #
    # @param hardware A hardware object.
    # @param parameters A parameters object.
    # @param parent The PyQt parent.
    #
    def __init__(self, hardware, parameters, parent):
        QtNetwork.QTcpServer.__init__(self, parent)
        self.port = hardware.tcp_port
        self.socket = None
        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        self.newConnection.connect(self.handleConnection)

        # Configure to listen on the appropriate port.
        self.listen(QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost), self.port)

    ## disconnect
    #
    # Forcibly disconnect from an external program.
    #
    @hdebug.debug
    def disconnect(self):
        if hdebug.getDebug():
            hdebug.logText(" TCPControl forced dis-connect. " + str(self.isConnected()))
        if self.isConnected():
            self.socket.disconnectFromHost()
            self.socket.waitForDisconnected()
            self.socket.close()
            self.socket = None
            self.listen(QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost), self.port)
            self.commLostConnection.emit()

    ## disconnected
    #
    # Called when the external program disconnects.
    #
    @hdebug.debug
    def disconnected(self):
        if hdebug.getDebug():
            hdebug.logText(" TCPControl lost connection. " + str(self.isConnected()))
        self.socket.disconnectFromHost()
        self.socket.close()
        self.socket = None
        self.commLostConnection.emit()

    ## handleConnection
    #
    # Called when a external program attempts to connect. If another
    # program is already connected then we tell the requestor that
    # we are busy and hangup. Otherwise we accept the connection.
    @hdebug.debug
    def handleConnection(self):
        if hdebug.getDebug():
            hdebug.logText(" TCPControl got connection. " + str(self.isConnected()))

        socket = self.nextPendingConnection()        
        if self.isConnected():
            print "  busy.."
            socket.write(QtCore.QByteArray("Busy\n"))
            socket.disconnectFromHost()
            socket.close()
        else:
            print "  connecting.."
            self.socket = socket
            self.socket.readyRead.connect(self.readyRead)
            self.socket.disconnected.connect(self.disconnected)
            self.commGotConnection.emit()

    ## isConnected
    #
    # Return True if an external program is connected, False otherwise.
    #
    # @return True/False depending on the connection state.
    #
    @hdebug.debug
    def isConnected(self):
        if self.socket and (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False

    ## readyRead
    #
    # Called when the external program sends a command. The command
    # is parsed to generate a PyQy signal based on the data contained
    # in the command. This also sends a response back to the external
    # program to acknowledge receipt of the command.
    #
    @hdebug.debug
    def readyRead(self):
        while self.socket.canReadLine():
            message = str(self.socket.readLine())[:-1]
            if hdebug.getDebug():
                hdebug.logText("Got: " + message)

            # Send an acknowledgement that the command was recieved.
            self.socket.write(QtCore.QByteArray("Ack\n"))
            self.socket.flush()

            # Parse the message to generate the command.
            message_split = message.split(",")

            # Get command type.
            command_type = message_split[0]

            # Parse command data.
            i = 0
            command_data = []
            message_data = message_split[1:]
            while(i < len(message_data)):
                m_type = message_data[i]
                m_value = message_data[i+1]

                if (m_type == "string"):
                    command_data.append(m_value)
                elif (m_type == "int"):
                    command_data.append(int(m_value))
                elif (m_type == "float"):
                    command_data.append(float(m_value))
                else:
                    print "Unknown type:", m_type
                i += 2

            self.commMessage.emit(TCPMessage(command_type, command_data))
     
    ## sendComplete
    #
    # Called to send a complete message back to the external program. This
    # is used by commands that may take a while to complete, such as taking
    # a movie.
    #
    # @param a_string Additional data as a string to send with the complete message.
    #
    @hdebug.debug
    def sendComplete(self, a_string):
        if self.isConnected():
            hdebug.logText("sendComplete " + a_string)
            self.socket.write(QtCore.QByteArray("Complete," + a_string + "\n"))
            self.socket.flush()
        else:
            hdebug.logText("sendComplete: not connected")


#
# testing
#

if __name__ == "__main__":
    app = QtCore.QCoreApplication(sys.argv)
    tcpControl = TCPControl(9000)
    app.exec_()
    sys.exit()


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

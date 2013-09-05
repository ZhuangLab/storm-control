#!/usr/bin/python
#
# Handles remote control (via TCP/IP of the data collection program)
#
# Hazen 8/13
#

import sys
from PyQt4 import QtCore, QtNetwork

def match(string1, string2):
    if len(string2) >= len(string1):
        if string1 == string2[0:len(string1)]:
            return 1
        else:
            return 0
    else:
        return 0


#
# TCP/IP Control Class
#
# To allow only one connection at a time from the local computer
# the server is closed once the connection is made. When the
# connection is broken the server is opened again.
#
class TCPControl(QtNetwork.QTcpServer):
    commGotConnection = QtCore.pyqtSignal()
    commLostConnection = QtCore.pyqtSignal()

    def __init__(self, port, parent = None):
        QtNetwork.QTcpServer.__init__(self, parent)
        self.debug = True
        self.port = port
        self.socket = None
        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        self.newConnection.connect(self.handleConnection)

        # Configure to listen on the appropriate port.
        self.listen(QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost), self.port)

    def isConnected(self):
        if self.socket and (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False

    def disconnect(self):
        if self.debug:
            print " TCPControl forced dis-connect.", self.isConnected()
        if self.isConnected():
            self.socket.disconnectFromHost()
            self.socket.waitForDisconnected()
            self.socket.close()
            self.socket = None
            self.listen(QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost), self.port)
            self.commLostConnection.emit()

    def disconnected(self):
        if self.debug:
            print " TCPControl lost connection.", self.isConnected()
        self.socket.disconnectFromHost()
        self.socket.close()
        self.socket = None
        self.commLostConnection.emit()
        
    def handleConnection(self):
        if self.debug:
            print " TCPControl got connection.", self.isConnected()

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
            
    def readyRead(self):
        while self.socket.canReadLine():
            command = str(self.socket.readLine())[:-1]
            if self.debug:
                print "Got: ", command

            # Send an acknowledgement that the command was recieved.
            self.socket.write(QtCore.QByteArray("Ack\n"))
            self.socket.flush()

            #
            # Parse the command to dynamically generate a PyQt signal.
            #
            # The idea is that this will eliminate this class as the
            # middleman. The sender can send arbitrary commands, this
            # class will generate the appropriate signal, and hopefully
            # it will be recognized by the appropriate recipient.
            #

            command_split = command.split(",")
            command_data = command_split[1:]
            signal = command_split[0] + "("
            i = 0
            parsed_data = []
            while(i < len(command_data)):
                type = command_data[i]
                value = command_data[i+1]
                if (type == "string"):
                    signal += "PyQt_PyObject,"
                    parsed_data.append(value)
                elif (type == "int"):
                    signal += "int,"
                    parsed_data.append(int(value))
                elif (type == "float"):
                    signal += "float,"
                    parsed_data.append(float(value))
                else:
                    print "Unknown type:", type
                i += 2

            if (len(signal) == len(command_split[0])+1):
                signal += ")"
            else:
                signal = signal[:-1] + ")"
            print signal
            self.emit(QtCore.SIGNAL(signal), *parsed_data)

    def sendComplete(self, a_string = "NA"):
        if self.isConnected():
            print "sendComplete", a_string
            self.socket.write(QtCore.QByteArray("Complete," + a_string + "\n"))
            self.socket.flush()
        else:
            print "sendComplete: not connected"

    def sendStatus(self, status):
        if self.debug:
            print "sendStatus"

        if self.isConnected():
            self.socket.write(QtCore.QByteArray("Status," + str(status)))
        else:
            print "sendStatus: not connected"


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

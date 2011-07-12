#!/usr/bin/python
#
# Handles remote control (via TCP/IP of the data collection program)
#
# Hazen 5/09
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
# This should only allow one connection at a time from the local computer.
#
class TCPControl(QtNetwork.QTcpServer):
    def __init__(self, port, parent = None):
        QtNetwork.QTcpServer.__init__(self, parent)
        self.debug = 1
        self.connected = 0
        self.socket = None
        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        self.connect(self, QtCore.SIGNAL("newConnection()"), self.handleConnection)

        # Configure to listen on the appropriate port.
        self.listen(QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost), port)

    def amConnected(self):
        if self.connected:
            return True
        else:
            return False

    def disconnect(self):
        if self.connected:
            self.connected = 0
            self.socket.close()
            self.emit(QtCore.SIGNAL("commLostConnection()"))

    def disconnected(self):
        if self.debug:
            print " TCPControl lost connection.", self.socket.state()
        self.connected = 0
        self.socket.close()
        self.emit(QtCore.SIGNAL("commLostConnection()"))
        
    def handleConnection(self):
        if self.debug:
            print " TCPControl got connection."
        if not self.connected:
            self.socket = self.nextPendingConnection()
            self.socket.connect(self.socket, QtCore.SIGNAL("readyRead()"), self.readyRead)
            self.socket.connect(self.socket, QtCore.SIGNAL("disconnected()"), self.disconnected)
            self.connected = 1
            self.emit(QtCore.SIGNAL("commGotConnection()"))

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

#            if match("abortMovie", command):
#                self.emit(QtCore.SIGNAL("commAbortMovie()"))
#                if self.debug:
#                    print " commAbortMovie"
#            elif match("incPower", command):
#                [channel, power_inc] = command.split(",")[1:]
#                self.emit(QtCore.SIGNAL("commIncPower(int, float)"), int(channel), float(power_inc))
#            elif match("movie", command):
#                [name, length] = command.split(",")[1:]
#                self.emit(QtCore.SIGNAL("commMovie(PyQt_PyObject, int)"), name, int(length))
#                if self.debug:
#                    print " commMovie", name, int(length)
#            elif match("moveTo", command):
#                [x, y] = command.split(",")[1:]
#                self.emit(QtCore.SIGNAL("commMoveTo(float, float)"), float(x), float(y))
#                if self.debug:
#                    print " commMoveTo", float(x), float(y)
#            elif match("parameters", command):
#                index = int(command.split(",")[1])
#                self.emit(QtCore.SIGNAL("commParameters(int)"), index)
#                if self.debug:
#                    print " commParameters", index
#            elif match("progressionLockout", command):
#                self.emit(QtCore.SIGNAL("commProgressionLockout()"))
#                if self.debug:
#                    print " commProgressionLockout"
#            elif match("setDirectory", command):
#                directory = command.split(",")[1]
#                self.emit(QtCore.SIGNAL("commSetDirectory(PyQt_PyObject)"), directory)
#                if self.debug:
#                    print " commSetDirectory", directory
#            elif match("setLockTarget", command):
#                target = command.split(",")[1]
#                self.emit(QtCore.SIGNAL("commSetLockTarget(float)"), float(target))
#                if self.debug:
#                    print " commSetLockTarget", float(target)
#            elif match("setPower", command):
#                [channel, power] = command.split(",")[1:]
#                self.emit(QtCore.SIGNAL("commSetPower(int, float)"), int(channel), float(power))
#            elif match("quit", command) and (not self.have_parent):
#                sys.exit()
#            else:
#                if self.debug:
#                    print " readyRead, no such command:", command

    def sendComplete(self):
        if self.debug:
            print "sendComplete"
        if self.connected:
            self.socket.write(QtCore.QByteArray("Complete\n"))
            self.socket.flush()

    def sendStatus(self, status):
        if self.debug:
            print "sendStatus"
        if self.connected:
            self.socket.write(QtCore.QByteArray("Status," + str(status)))

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
# Copyright (c) 2009 Zhuang Lab, Harvard University
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

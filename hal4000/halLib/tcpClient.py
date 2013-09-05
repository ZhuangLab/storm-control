#!/usr/bin/python
#
# TCP interface to HAL-4000 data taking program 
# for the Dave command scripting program.
#
# Hazen 12/13
#

import sys
import time
from PyQt4 import QtCore, QtGui, QtNetwork


# The socket for communication with HAL-4000
class HALSocket(QtNetwork.QTcpSocket):
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(str)

    def __init__(self, port):
        QtNetwork.QTcpSocket.__init__(self)
        self.port = port

        # signals
        self.readyRead.connect(self.handleReadyRead)

    def connectToHAL(self):
        # try to make connection
        addr = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost)
        self.connectToHost(addr, self.port)
        tries = 0
        while (not self.waitForConnected() and (tries < 5)):
            print " Couldn't connect to HAL-4000, waiting 1 second and retrying"
            time.sleep(1)
            tries += 1
            self.connectToHost(addr, self.port)

        if (tries == 5):
            print " Could not connect to HAL-4000."
        else:
            print " Connected to HAL-4000."

    def handleReadyRead(self):
        while self.canReadLine():
            line = str(self.readLine()).strip()            
            if (line == "Ack"):
                self.acknowledged.emit()
            elif (line[0:8] == "Complete"):
                values = line.split(",")
                if (len(values)==2):
                    self.complete.emit(values[1])
                else:
                    self.complete.emit("NA")
            elif (line == "Busy"):
                self.socket.disconnectFromHost()

    def sendCommand(self, command):
        self.write(QtCore.QByteArray(command + "\n"))


# Communication wrapper class
class TCPClient(QtGui.QWidget):
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(str)
    disconnect = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.socket = HALSocket(9000)
        self.state = None
        self.testing = False
        self.unacknowledged = 0

        self.socket.acknowledged.connect(self.handleAcknowledged)
        self.socket.complete.connect(self.handleComplete)
        self.socket.disconnected.connect(self.handleDisconnect)

    def handleAcknowledged(self):
        self.unacknowledged -= 1
        print "  got response", self.unacknowledged
        if (self.unacknowledged == 0):
            print " acknowledged"
            self.acknowledged.emit()
        
    def handleComplete(self, a_string):
        if (self.state == "filming"):
            print " movie complete", a_string
        elif (self.state == "finding_sum"):
            print " finding sum complete", a_string
        elif (self.state == "recentering"):
            print " recentering complete", a_string
        else:
            print " unknown state:", self.state
        self.complete.emit(a_string)
        self.state = None

    def handleDisconnect(self):
        self.disconnect.emit()

    def isConnected(self):
        if (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False

    def sendCommand(self, command):
        if self.isConnected():
            print "  sending:", command
            self.unacknowledged += 1
            self.socket.sendCommand(command)
            self.socket.flush()
            time.sleep(0.05)
        else:
            print " Not connected?!?"

    #
    # Fire all the settings off at once...
    #
    def sendMovieParameters(self, movie):

        # send parameters index.
        if hasattr(movie, "parameters"):
            self.sendCommand("parameters,int,{0:d}".format(movie.parameters))

        # send stage position.
        if hasattr(movie, "stage_x") and hasattr(movie, "stage_y"):
            self.sendCommand("moveTo,float,{0:.2f},float,{1:.2f}".format(movie.stage_x, movie.stage_y))

        # send lock target.
        if hasattr(movie, "lock_target"):
            self.sendCommand("setLockTarget,float,{0:.1f}".format(movie.lock_target))

    def sendSetDirectory(self, directory):
        self.sendCommand("setDirectory,string,{0:s}".format(directory))

    def startCommunication(self):
        print " starting communications", self.isConnected()
        if not self.isConnected():
            self.socket.connectToHAL()
            self.unacknowledged = 0

    def startFindSum(self):
        print " start find sum"
        self.state = "finding_sum"
        self.sendCommand("findSum")

    def startMovie(self, movie):
        print " start movie"
        if hasattr(movie, "progression"):
            if (movie.progression.type == "lockedout"):
                self.sendCommand("progressionLockout")
            elif (movie.progression.type != "none"):
                self.sendCommand("progressionType,string,{0:s}".format(movie.progression.type))
                # Power controlled by file.
                if movie.progression.type == "file":
                    self.sendCommand("progressionFile,string,{0:s}".format(movie.progression.filename))
                else:
                    for channel in movie.progression.channels:
                        # Power controlled by progression dialog box settings.
                        if channel[2]:
                            self.sendCommand("progressionSet,int,{0:d},float,{1:.4f},int,{2:d},float,{3:.4f}".format(channel[0],
                                                                                                                     channel[1],
                                                                                                                     channel[2],
                                                                                                                     channel[3]))
                        # Fixed power.
                        else:
                            self.sendCommand("setPower,int,{0:d},float,{1:.4f}".format(channel[0], channel[1]))
        self.state = "filming"
        self.sendCommand("movie,string,{0:s},int,{1:d}".format(movie.name, movie.length))

    def startRecenterPiezo(self):
        print " start recenter piezo"
        self.state = "recentering"
        self.sendCommand("recenterPiezo")

    def stopCommunication(self):
        print " stopping communications", self.isConnected()
        if self.isConnected():
            self.socket.disconnectFromHost()
            #self.socket.waitForDisconnected()
            print "  ", self.isConnected()

    def stopMovie(self):
        print " stop movie"
        self.sendCommand("abortMovie")

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

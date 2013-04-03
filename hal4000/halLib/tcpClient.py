#!/usr/bin/python
#
# TCP interface to HAL-4000 data taking program 
# for the Dave command scripting program.
#
# Hazen 12/10
#

import sys
import time
from PyQt4 import QtCore, QtGui, QtNetwork


# The socket for communication with HAL-4000
class HALSocket(QtNetwork.QTcpSocket):
    def __init__(self, port):
        QtNetwork.QTcpSocket.__init__(self)

        # signals
        self.connect(self, QtCore.SIGNAL("readyRead()"), self.handleReadyRead)

        # try to make connection
        addr = QtNetwork.QHostAddress(QtNetwork.QHostAddress.LocalHost)
        self.connectToHost(addr, port)
        while not self.waitForConnected():
            print "Couldn't connect to HAL-4000, waiting 1 second and retrying"
            time.sleep(1)
            self.connectToHost(addr, port)

    def handleReadyRead(self):
        while self.canReadLine():
            line = str(self.readLine()).strip()
            if line == "Ack":
                self.emit(QtCore.SIGNAL("acknowledged()"))
            if line == "Complete":
                self.emit(QtCore.SIGNAL("complete()"))

    def sendCommand(self, command):
        self.write(QtCore.QByteArray(command + "\n"))


# Communication wrapper class
class TCPClient(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.connected = 0
        self.state = None
        self.testing = 0
        self.unacknowledged = 0

        # For testing without actually talking to HAL-4000
        if self.testing:
            self.testing_timer = QtCore.QTimer(self)
            self.testing_timer.setInterval(5000)
            self.testing_timer.setSingleShot(True)
            self.connect(self.testing_timer, 
                         QtCore.SIGNAL("timeout()"),
                         self.handleComplete)

    def handleAcknowledged(self):
        self.unacknowledged -= 1

    def handleComplete(self):
        if (self.state == "filming"):
            print " movie complete"
        elif (self.state == "finding_sum"):
            print " finding sum complete"
        elif (self.state == "recentering"):
            print " recentering complete"
        else:
            print " unknown state:", self.state
        self.emit(QtCore.SIGNAL("complete()"))
        self.state = None

    def sendCommand(self, command):
        if self.connected:
            self.unacknowledged += 1
            self.socket.sendCommand(command)
            self.socket.flush()
            time.sleep(0.05)
            print " sent command:", command
        else:
            print " Not connected?!?"

    def sendInitialPowers(self, movie):
        if self.testing:
            print " sending initial powers"

    # Fire all the data off at once...
    def sendMovieParameters(self, movie):
        if self.testing:
            print " sending movie parameters"
        else:
            if self.unacknowledged != 0:
                print self.unacknowledged, "commands are still pending"
            # send parameters index.
            if hasattr(movie, "parameters"):
                self.sendCommand("parameters,int,{0:d}".format(movie.parameters))
            # send stage position.
            if hasattr(movie, "stage_x") and hasattr(movie, "stage_y"):
                self.sendCommand("moveTo,float,{0:.2f},float,{1:.2f}".format(movie.stage_x, movie.stage_y))
            # send lock target.
            if hasattr(movie, "lock_target"):
                self.sendCommand("setLockTarget,float,{0:.1f}".format(movie.lock_target))

    def sendPowerUpdate(self, channel, power_increment):
        if self.testing:
            print " send power update", channel, power_increment
        else:
            self.sendCommand("incPower,int,{0:d},float,{1:.4f}".format(channel, power_increment))

    def sendSetDirectory(self, directory):
        if self.testing:
            print " send set directory", directory
        else:
            self.sendCommand("setDirectory,string,{0:s}".format(directory))

    def startCommunication(self):
        print " starting communications"
        self.socket = HALSocket(9000)
        self.connected = 1
        self.unacknowledged = 0
        self.connect(self.socket, QtCore.SIGNAL("acknowledged()"), self.handleAcknowledged)
        self.connect(self.socket, QtCore.SIGNAL("complete()"), self.handleComplete)

    def startFindSum(self):
        print " start find sum"
        self.state = "finding_sum"
        self.sendCommand("findSum")

    def startMovie(self, movie):
        print " start movie"
        if self.testing:
            self.testing_timer.start()
        else:
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
        print " stopping communications"
        if self.unacknowledged == 0:
            self.socket.disconnectFromHost()
            return True
        else:
            return False

    def stopMovie(self):
        print " stop movie"
        if self.testing:
            self.testing_timer.stop()
            self.emit(QtCore.SIGNAL("movieComplete()"))
        else:
            self.sendCommand("abortMovie")

#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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

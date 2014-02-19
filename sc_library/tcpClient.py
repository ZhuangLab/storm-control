#!/usr/bin/python
#
## @file
#
# TCP interface to HAL-4000 data taking program 
# for the Dave command scripting program.
#
# Hazen 12/13
#

import sys
import time
from PyQt4 import QtCore, QtGui, QtNetwork

import sc_library.hdebug as hdebug

## HALSocket
#
# The socket for communication with HAL-4000
#
class HALSocket(QtNetwork.QTcpSocket):
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(str)

    ## __init__
    #
    # @param port The TCP/IP port to communicate on. Usually this is 9000.
    #
    @hdebug.debug
    def __init__(self, port):
        QtNetwork.QTcpSocket.__init__(self)
        self.port = port

        # signals
        self.readyRead.connect(self.handleReadyRead)

    ## connectToHal
    #
    # Try to make a connection to the HAL software.
    #
    @hdebug.debug
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

    ## handleReadyRead
    #
    # This is called when there is new data available HAL on the TCP/IP connection.
    # Depending on the data it emits the appropriate signal.
    #
    @hdebug.debug
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

    ## sendCommand
    #
    # Sends a command to HAL.
    #
    # @param command The command to send (as a string).
    #
    @hdebug.debug
    def sendCommand(self, command):
        self.write(QtCore.QByteArray(command + "\n"))


## TCPClient
#
# Communication wrapper class
#
class TCPClient(QtGui.QWidget):
    acknowledged = QtCore.pyqtSignal()
    complete = QtCore.pyqtSignal(str)
    disconnect = QtCore.pyqtSignal()

    ## __init__
    #
    # Open a connection to HAL (A HALSocket) and connect the signals.
    #
    @hdebug.debug
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.comm_state = None
        self.socket = HALSocket(9000)
        self.testing = False
        self.unacknowledged = 0

        self.socket.acknowledged.connect(self.handleAcknowledged)
        self.socket.complete.connect(self.handleComplete)
        self.socket.disconnected.connect(self.handleDisconnect)

    ## handleAcknowledged
    #
    # Handles the acknowledged signal from the HAL socket.
    #
    @hdebug.debug
    def handleAcknowledged(self):
        self.unacknowledged -= 1
        hdebug.logText("  got response " + str(self.unacknowledged))
        if (self.unacknowledged == 0):
            hdebug.logText(" acknowledged")
            self.acknowledged.emit()

    ## handleComplete
    #
    # Handles the complete signal from the HAL socket.
    #
    @hdebug.debug
    def handleComplete(self, a_string):
        if (self.comm_state == "filming"):
            hdebug.logText(" movie complete " + a_string)
        elif (self.comm_state == "finding_sum"):
            hdebug.logText(" finding sum complete " + a_string)
        elif (self.comm_state == "recentering"):
            hdebug.logText(" recentering complete " + a_string)
        else:
            hdebug.logText(" unknown state: " + str(self.comm_state))
        self.comm_state = None
        self.complete.emit(a_string)

    ## handleDisconnect
    #
    # Handles the disconnect signal from the HAL socket.
    #
    @hdebug.debug
    def handleDisconnect(self):
        self.disconnect.emit()

    ## isConnected
    #
    # @return True/False is the HAL socket actually connected to HAL.
    #
    @hdebug.debug
    def isConnected(self):
        if (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            return True
        else:
            return False

    ## sendCommand
    #
    # Sends a command to HAL via the HAL socket.
    #
    # @param command The command to send (as a string).
    #
    @hdebug.debug
    def sendCommand(self, command):
        if self.isConnected():
            hdebug.logText("  sending: " + command)
            self.unacknowledged += 1
            self.socket.sendCommand(command)
            self.socket.flush()
            time.sleep(0.05)
        else:
            hdebug.logText(" Not connected?!?")

    ## sendMovieParameters
    #
    # Sends the parameters for a movie to HAL. This fires all the settings off at once...
    #
    # @param movie A movie object.
    #
    @hdebug.debug
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

    ## sendSetDirectory
    #
    # Tells HAL to change the current working directory.
    #
    # @param directory The new directory (as a string).
    #
    @hdebug.debug
    def sendSetDirectory(self, directory):
        self.sendCommand("setDirectory,string,{0:s}".format(directory))

    ## startCommunication
    #
    # This tells the HAL socket to make a connection to HAL.
    #
    @hdebug.debug
    def startCommunication(self):
        hdebug.logText(" starting communications " + str(self.isConnected()))
        if not self.isConnected():
            self.socket.connectToHAL()
            self.unacknowledged = 0

    ## startFindSum
    #
    # Tells HAL to start the focus lock find sum procedure.
    #
    @hdebug.debug
    def startFindSum(self):
        hdebug.logText(" start find sum")
        self.comm_state = "finding_sum"
        self.sendCommand("findSum")

    ## startMovie
    #
    # Configures HAL progressions and starts acquiring a movie.
    #
    # @param movie A movie object.
    #
    @hdebug.debug
    def startMovie(self, movie):
        hdebug.logText(" start movie")
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
        self.comm_state = "filming"
        self.sendCommand("movie,string,{0:s},int,{1:d}".format(movie.name, movie.length))

    ## startRecenterPiezo
    #
    # Tell HAL to recenter the focus lock piezo. This won't do anything if the
    # microscope does not have a motorized Z.
    #
    @hdebug.debug
    def startRecenterPiezo(self):
        hdebug.logText(" start recenter piezo")
        self.comm_state = "recentering"
        self.sendCommand("recenterPiezo")

    ## stopCommunication
    #
    # Tell the HAL socket to break the connection to HAL.
    #
    @hdebug.debug
    def stopCommunication(self):
        hdebug.logText(" stopping communications " + str(self.isConnected()))
        if self.isConnected():
            self.socket.disconnectFromHost()
            #self.socket.waitForDisconnected()
            hdebug.logText("  " + str(self.isConnected()))

    ## stopMovie
    #
    # Tell HAL to stop taking the current movie.
    #
    @hdebug.debug
    def stopMovie(self):
        hdebug.logText(" stop movie")
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

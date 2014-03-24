#!/usr/bin/python
#
## @file 
#
# Handles remote control (via TCP/IP of the data collection program)
#
# Hazen 02/14
#

import halLib.halModule as halModule

import sc_library.hdebug as hdebug
from sc_library.tcpServer import TCPServer

## TCP/IP Control Class
#
# To allow only one connection at a time from the local computer
# the server is closed once the connection is made. When the
# connection is broken the server is opened again.
#
class HalTCPControl(TCPServer, halModule.HalModule):

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
        TCPServer.__init__(self,
                           port = hardware.tcp_port,
                           server_name = "Hal",
                           parent = parent,
                           verbose = True)
        halModule.HalModule.__init__(self)

    ## connectSignals
    #
    # @param signals An array of signals that we might be interested in connecting to.
    #
    @hdebug.debug
    def connectSignals(self, signals):
        for signal in signals:
            if (signal[1] == "tcpComplete"):
                signal[2].connect(self.sendMessage)

    ## getSignals
    #
    # @return The signals this module provides.
    #
    @hdebug.debug
    def getSignals(self):
        return [[self.hal_type, "commGotConnection", self.comGotConnection],
                [self.hal_type, "commLostConnection", self.comLostConnection],
                [self.hal_type, "commMessage", self.messageReceived]]

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

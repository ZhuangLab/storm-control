#!/usr/bin/python
#
## @file
#
# Thread for handling communication with a bluetooth device, an
# android phone for example. It is recommended that your devices
# support at least Bluetooth version 2.0 if you want to send the
# current camera display from HAL to the device.
#
# Hazen 02/14
#

import bluetooth
from cStringIO import StringIO
from PyQt4 import QtCore

import halLib.halModule as halModule

import sc_library.hdebug as hdebug

## HalBluetooth
#
# QThread for communication with a bluetooth device.
#
class HalBluetooth(QtCore.QThread, halModule.HalModule):

    ## __init__
    #
    # @param hardware A hardware object.
    # @param parameters A parameters object.
    # @param parent The PyQt parent.
    #
    def __init__(self, hardware, parameters, parent):
        QtCore.QThread.__init__(self, parent)
        halModule.HalModule.__init__(self)

        self.connected = False
        self.mutex = QtCore.QMutex
        self.send_pictures = hardware.send_pictures
        
        # Setup bluetooth socket.
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_sock.bind(("",bluetooth.PORT_ANY))
        self.server_sock.listen(1)

        port = self.server_sock.getsockname()[1]
        hdebug.logText("Waiting for connection on RFCOMM channel {0:d}".format(port))

        uuid = "3e1f9ea8-9c11-11e3-b248-425861b86ab6"

        bluetooth.advertise_service( self.server_sock, "halServer",
                                     service_id = uuid,
                                     service_classes = [ uuid, bluetooth.SERIAL_PORT_CLASS ],
                                     profiles = [ bluetooth.SERIAL_PORT_PROFILE ],
                                     )
        self.server_sock.settimeout(0.5)
        print "timeout:", self.server_sock.gettimeout()

        self.start(QtCore.QThread.NormalPriority)

    ## cleanup
    #
    # Stop the thread.
    #
    def cleanup(self):
        self.quit()

    ## run
    #
    # Loop, waiting for connections or data.
    #
    def run(self):
        while True:
            [client_sock, client_info] = self.server_sock.accept()
            hdebug.logText("Connected to", client_info)
            self.connected = True
            while self.connected:
                data = client_sock.recv(1024)
                if (len(data) == 0):
                    print "lost connection?"
                    self.connected = False
                print "received", data

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

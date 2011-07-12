#!/usr/bin/python
#
# Handles telling the acquisition program to get
# a picture & converts the captured image into a
# QPixmap.
#
# Hazen 12/09
#

import numpy
import time

from collections import deque
from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# Communication with the acquisition software
import lib.tcpClient

# Reading DAX files
import lib.daxspereader

#
# Movie class for use w/ tcpClient
#
class Movie():
    def __init__(self, name, stagex, stagey):
        self.stage_x = float(stagex)
        self.stage_y = float(stagey)

        self.name = name
        self.length = 1
        self.progressions = []

#
# Capture
#
class Capture(QtCore.QObject):
    @hdebug.debug
    def __init__(self, parameters):
        QtCore.QObject.__init__(self)
        self.capturing = False
        self.dax = None
        self.directory = parameters.directory
        self.filename = parameters.image_filename
        self.pixmaps = deque() # In the future we might support queuing captures?
        
        self.tcp_client = lib.tcpClient.TCPClient()
        self.connect(self.tcp_client, QtCore.SIGNAL("complete()"), self.captureDone)
        self.connected = False

    @hdebug.debug
    def captureDone(self):
        # load the first frame of the dax file
        filename = self.directory + self.filename + ".dax"
        success = False

        # Deals with a file system race condition?
        # Or is it a acquisition software problem?
        time.sleep(0.05)
        tries = 0
        while (not success) and (tries < 4):
            try:
                self.dax = lib.daxspereader.DaxReader(filename, verbose = 1)
                frame = self.dax.loadAFrame(0).astype(numpy.float)
                success = True
            except:
                print "Failed to load:", filename
                frame = None
                time.sleep(0.05)
            tries += 1
        self.capturing = False
        
        if type(frame) == type(numpy.array([])):
            # scale to match the view when saved & threshold it
            scale = self.dax.filmScale()
            frame = 255.0 * (frame - float(scale[0]))/float(scale[1] - scale[0])
            frame[(frame > 255.0)] = 255.0
            frame[(frame < 0.0)] = 0.0

            # transform to match the camera view
            frame = numpy.transpose(frame).copy()

            # convert to QPixmap
            frame = frame.astype(numpy.uint8)
            w, h = frame.shape
            image = QtGui.QImage(frame.data, w, h, QtGui.QImage.Format_Indexed8)
            image.ndarray = frame
            for i in range(256):
                image.setColor(i, QtGui.QColor(i,i,i).rgb())
            self.pixmaps.append(QtGui.QPixmap.fromImage(image))

            # get location & emit signal
            [x, y] = self.dax.filmLocation()
            self.emit(QtCore.SIGNAL("captureComplete(float, float)"), x, y)

    @hdebug.debug
    def captureStart(self, stagex, stagey):
        if not self.capturing and self.connected:
            self.capturing = True
            self.movie = Movie(self.filename, stagex, stagey)
            self.tcp_client.sendMovieParameters(self.movie)
            # depending on how far we could perhaps handle this more intelligently?
            time.sleep(0.5)
            self.tcp_client.startMovie(self.movie)
        else:
            print "Disconnected? Busy?"

    @hdebug.debug
    def commConnect(self):
        if not self.connected:
            self.tcp_client.startCommunication()
            self.connected = True
            self.tcp_client.sendSetDirectory(self.directory[:-1])

    @hdebug.debug
    def commDisconnect(self):
        if self.connected:
            self.tcp_client.stopCommunication()
            self.connected = False

    @hdebug.debug
    def currentPixmap(self):
        return self.pixmaps.popleft()

    @hdebug.debug
    def gotoPosition(self, stagex, stagey):        
        if not self.capturing and self.connected:
            self.movie = Movie(self.filename, stagex, stagey)
            self.tcp_client.sendMovieParameters(self.movie)
        else:
            print "Disconnected? Busy?"

    def setDirectory(self, directory):
        self.directory = directory
        if self.connected:
            self.tcp_client.sendSetDirectory(self.directory[:-1])

    def shutDown(self):
        self.commDisconnect()

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

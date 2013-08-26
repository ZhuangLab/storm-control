#!/usr/bin/python
#
# Handles telling the acquisition program to get
# a picture & converts the captured image into a
# QPixmap.
#
# Hazen 02/13
#

import math
import numpy
import time

from PyQt4 import QtCore, QtGui

# Debugging
import halLib.hdebug as hdebug

# Communication with the acquisition software
import halLib.tcpClient

# Reading DAX files
import halLib.daxspereader

import coord

#
# Image class for temporary storage of image data.
#
class Image():
    def __init__(self, data, size, display_scale, location, params):
        self.data = data
        self.height = size[1]
        self.image_min = display_scale[0]
        self.image_max = display_scale[1]
        self.parameters_file = params
        self.width = size[0]

        # FIXME: Should we flip x and y?
        self.x_um = location[0]
        self.y_um = location[1]

        # Calculate location in pixels.
        a_point = coord.Point(self.x_um, self.y_um, "um")
        self.x_pix = a_point.x_pix
        self.y_pix = a_point.y_pix

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
    captureComplete = QtCore.pyqtSignal(object)

    @hdebug.debug
    def __init__(self, parameters):
        QtCore.QObject.__init__(self)
        self.capturing = False
        self.curr_x = 0.0
        self.curr_y = 0.0
        self.dax = None
        self.directory = parameters.directory
        self.goto = False
        self.filename = parameters.image_filename
        self.flip_horizontal = parameters.flip_horizontal
        self.flip_vertical = parameters.flip_vertical
        self.movies_remaining = 0
        self.stage_speed = parameters.stage_speed
        self.start_timer = QtCore.QTimer(self)

        self.start_timer.setSingleShot(True)
        self.start_timer.timeout.connect(self.handleStartTimer)

        self.tcp_client = halLib.tcpClient.TCPClient()
        self.tcp_client.acknowledged.connect(self.handleAcknowledged)
        self.tcp_client.complete.connect(self.captureDone)
        self.tcp_client.disconnect.connect(self.handleDisconnect)
        self.connected = False

    def abort(self):
        if self.capturing:
            self.movies_remaining = 0

    @hdebug.debug
    def captureDone(self, a_string):

        # load the first frame of the dax file
        filename = self.directory + self.filename + ".dax"
        success = False

        # Deals with a file system race condition?
        # Or is it a acquisition software problem?
        time.sleep(0.05)
        tries = 0
        while (not success) and (tries < 4):
            try:
                self.dax = halLib.daxspereader.DaxReader(filename, verbose = 1)
                frame = self.dax.loadAFrame(0).astype(numpy.float)
                success = True
            except:
                print "Failed to load:", filename
                frame = None
                time.sleep(0.05)
            tries += 1

        self.capturing = False

        if (self.movies_remaining == 0):
            print "captureDone disconnect"
            self.commDisconnect()
        
        if type(frame) == type(numpy.array([])):
            if self.flip_horizontal:
                frame = numpy.fliplr(frame)
            if self.flip_vertical:
                frame = numpy.flipud(frame)
            image = Image(frame,
                          self.dax.filmSize(),
                          self.dax.filmScale(),
                          self.dax.filmLocation(),
                          self.dax.filmParameters())

            self.captureComplete.emit(image)

    @hdebug.debug
    def captureStart(self, stagex, stagey, movies_remaining):
        if not self.capturing:
            self.movies_remaining = movies_remaining

            if not self.connected:
                self.commConnect(True)

            if self.connected:
                # set up for capture
                self.capturing = True
                self.movie = Movie(self.filename, stagex, stagey)
                self.tcp_client.sendMovieParameters(self.movie)

                # determine how long to wait, depending on stage speed.
                dist_x = stagex - self.curr_x
                dist_y = stagey - self.curr_y
                dist = math.sqrt(dist_x*dist_x + dist_y*dist_y)
                sleep_time = 0.001 * (dist/self.stage_speed) + 1.0
                self.start_timer.setInterval(1000.0 * sleep_time)
                self.start_timer.start()

                # record current position
                self.curr_x = stagex
                self.curr_y = stagey
        else:
            print "Busy?"

    @hdebug.debug
    def commConnect(self, set_directory = False):
        self.tcp_client.startCommunication()
        self.connected = self.tcp_client.getConnected()
        if self.connected and set_directory:
            self.tcp_client.sendSetDirectory(self.directory[:-1])

    @hdebug.debug
    def commDisconnect(self):
        self.tcp_client.stopCommunication()
        self.connected = False

    @hdebug.debug
    def gotoPosition(self, stagex, stagey):
        #if ((not self.capturing) and (self.movies_remaining == 0)):
        if not self.capturing:
            if not self.connected:
                self.commConnect()
            if self.connected:
                self.movie = Movie(self.filename, stagex, stagey)
                self.tcp_client.sendMovieParameters(self.movie)
                self.goto = True
        else:
            print "Busy?"

    def handleAcknowledged(self):
        if self.goto:
            print "handleAcknowledged disconnect"
            self.commDisconnect()
            self.goto = False

    def handleDisconnect(self):
        self.capturing = False
        self.connected = False

    def handleStartTimer(self):
        if self.connected and self.capturing:
            self.tcp_client.startMovie(self.movie)

    def setDirectory(self, directory):
        self.directory = directory

    def shutDown(self):
        if self.connected:
            self.commDisconnect()

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

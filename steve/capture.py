#!/usr/bin/python
#
## @file
#
# Handles telling the acquisition program to get
# a picture & converts the captured image into a
# QPixmap.
#
# Hazen 03/14
#

import math
import numpy
import os
import time

from PyQt4 import QtCore, QtGui

# Debugging
import sc_library.hdebug as hdebug

# Communication with the acquisition software
import sc_library.tcpClient as tcpClient
import sc_library.tcpMessage as tcpMessage

# Reading DAX files
import sc_library.daxspereader as daxspereader

import coord


## directoryMessage
#
# Creates a change directory message.
#
# @param directory The directory to change to.
#
# @return A TCPMessage object.
#
def directoryMessage(directory):
    return tcpMessage.TCPMessage(message_type = "Set Directory",
                                 message_data = {"directory" : directory})

## getPositionMessage
#
# Creates a get stage position message for communication via TCPClient.
#
# @return A TCPMessage object.
#
def getPositionMessage():
    return tcpMessage.TCPMessage(message_type = "Get Stage Position")

## movieMessage
#
# Creates a movie message for communication via TCPClient.
#
# @param filename The name of the movie.
#
# @return A TCPMessage object.
#
def movieMessage(filename):
    return tcpMessage.TCPMessage(message_type = "Take Movie",
                                 message_data = {"name" : filename,
                                                 "length" : 1})

## moveStageMessage
#
# Creates a stage message for communication via TCPClient.
#
# @param stagex The stage x coordinate.
# @param stagey The stage y coordinate.
#
# @return A TCPMessage object.
#
def moveStageMessage(stagex, stagey):  
    return tcpMessage.TCPMessage(message_type = "Move Stage",
                                 message_data = {"stage_x":stagex,
                                                 "stage_y":stagey})


## Image
#
# Image class for temporary storage of image data.
#
class Image():

    ## __init__
    #
    # @param data The image data (a numpy array).
    # @param size [image width, image height, number of frames].
    # @param display_scale [image value that equals 0, image value that equals 255].
    # @param location [stage x, stage y].
    # @param params The HAL xml file that was used to acquire the image.
    #
    def __init__(self, data, size, display_scale, location, params):
        self.data = data
        self.height = size[0]
        self.image_min = display_scale[0]
        self.image_max = display_scale[1]
        self.parameters_file = params
        self.width = size[1]

        self.x_um = location[0]
        self.y_um = location[1]

        # Calculate location in pixels.
        a_point = coord.Point(self.x_um, self.y_um, "um")
        self.x_pix = a_point.x_pix
        self.y_pix = a_point.y_pix

    ## __repr__
    #
    def __repr__(self):
        return hdebug.objectToString(self, "capture.Image", ["height", "width", "x_um", "y_um"])

## Capture
#
# Handles capturing images from HAL. Instructions to HAL about how
# to take the image are sent by TCP/IP. Once the image is acquired
# it is read from the disc (and not communicated directly back to
# this program).
#
# The TCP/IP connection is made and broken for each request (take a
# movie or move to a position). This is done for user convenience
# because when the connection is active some features of HAL, such 
# as movie acquisition, are locked out.
#
class Capture(QtCore.QObject):
    captureComplete = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal()
    getPositionComplete = QtCore.pyqtSignal(object)
    gotoComplete = QtCore.pyqtSignal()

    ## __init__
    #
    # @param parameters A parameters xml object.
    #
    @hdebug.debug
    def __init__(self, parameters):
        QtCore.QObject.__init__(self)
        self.curr_x = 0.0
        self.curr_y = 0.0
        self.dax = None
        self.directory = parameters.directory
        self.goto = False
        self.filename = parameters.image_filename
        self.flip_horizontal = parameters.flip_horizontal
        self.flip_vertical = parameters.flip_vertical
        self.messages = []
        self.transpose = parameters.transpose
        self.waiting_for_response = False

        self.tcp_client = tcpClient.TCPClient(parent = self,
                                              port = 9000,
                                              server_name = "hal",
                                              verbose = True)
        self.tcp_client.comLostConnection.connect(self.handleDisconnect)
        self.tcp_client.messageReceived.connect(self.handleMessageReceived)
        self.connected = False

    ## captureDone
    #
    # This is called when we get the (movie) completion method from HAL. It
    # attempts to find the image that HAL just took on the disk, creates a
    # Image object and emits the captureComplete signal.
    #
    # @param a_string Not used.
    #
    @hdebug.debug
    def captureDone(self):
        print "captureDone"

        # Load image.
        self.loadImage(self.fullname())

    ## captureStart
    #
    # Called to take a image at stagex, stagey. This tells HAL to move,
    # then when HAL returns that the move is complete an image is taken.
    #
    # @param stagex The x position to take the image at.
    # @param stagey The y position to take the image at.
    #
    @hdebug.debug
    def captureStart(self, stagex, stagey):
        
        if os.path.exists(self.fullname()):
            os.remove(self.fullname())
        
        if not self.tcp_client.isConnected():
            hdebug.logText("captureStart: not connected to HAL.")
            return False

        self.messages.append(moveStageMessage(stagex, stagey))
        self.messages.append(movieMessage(self.filename))
        self.sendFirstMessage()
        return True

    ## commConnect
    #
    # Initiate communication with HAL.
    #
    @hdebug.debug
    def commConnect(self):
        print "connect"
        self.tcp_client.startCommunication()

    ## commDisconnect
    #
    # Stop communication with HAL.
    #
    @hdebug.debug
    def commDisconnect(self):
        print "disconnect"
        self.tcp_client.stopCommunication()

    ## fullname
    #
    # returns the filename with path & extension.
    #
    # @return The filename with path & extension as a string.
    #
    @hdebug.debug
    def fullname(self):
        return self.directory + self.filename + ".dax"

    ## getPosition
    #
    # Called to query HAL about the current stage position.
    #
    @hdebug.debug
    def getPosition(self):

        if not self.tcp_client.isConnected():
            hdebug.logText("getPosition: not connected to HAL.")
            return

        message = getPositionMessage()
        self.messages.append(message)
        self.sendFirstMessage()

    ## gotoPosition
    #
    # Called to move to stagex, stagey.
    #
    # @param stagex The x position to move to.
    # @param stagey The y position to move to.
    #
    @hdebug.debug
    def gotoPosition(self, stagex, stagey):

        if not self.tcp_client.isConnected():
            hdebug.logText("gotoPosition: not connected to HAL.")
            return

        message = moveStageMessage(stagex, stagey)
        message.addData("is_goto", True)
        self.messages.append(message)
        self.sendFirstMessage()

    ## handleDisconnect
    #
    # Called when HAL disconnects.
    #
    @hdebug.debug
    def handleDisconnect(self):
        self.waiting_for_response = False
        self.messages = []
        self.disconnected.emit()

    ## handleMessageReceived
    #
    # Handles the messageReceived signal from the TCPClient.
    #
    # @param message A TCPMessage object.
    #
    @hdebug.debug
    def handleMessageReceived(self, message):
        if message.hasError():
            hdebug.logText("tcp error: " + message.getErrorMessage())
            self.messages = []
            self.waiting_for_response = False
            return

        if (message.getData("is_goto") == True):
            self.gotoComplete.emit()

        if (message.getType() == "Get Stage Position"):
            a_point = coord.Point(message.getResponse("stage_x"),
                                  message.getResponse("stage_y"),
                                  "um")
            self.getPositionComplete.emit(a_point)

        if (message.getType() == "Take Movie"):
            self.loadImage(self.directory + message.getData("name") + ".dax")

        if (len(self.messages) > 0):
            self.tcp_client.sendMessage(self.messages.pop(0))
        else:
            self.waiting_for_response = False

    ## loadImage
    #
    # Load a dax image. This is called by captureDone to
    # load the image. It is also called directly by Steve
    # to load images chosen by the user.
    #
    @hdebug.debug
    def loadImage(self, filename):
        success = False

        # Deals with a file system race condition?
        # Or is it a acquisition software problem?
        time.sleep(0.05)
        tries = 0
        while (not success) and (tries < 4):
            try:
                self.dax = daxspereader.DaxReader(filename, verbose = 1)
                frame = self.dax.loadAFrame(0)
                self.dax.closeFilePtr()
                success = True
            except:
                print "Failed to load:", filename
                frame = None
                time.sleep(0.05)
            tries += 1

        if type(frame) == type(numpy.array([])):
            if self.flip_horizontal:
                frame = numpy.fliplr(frame)
            if self.flip_vertical:
                frame = numpy.flipud(frame)
            if self.transpose:
                frame = numpy.transpose(frame)
            image = Image(frame,
                          self.dax.filmSize(),
                          self.dax.filmScale(),
                          self.dax.filmLocation(),
                          self.dax.filmParameters())

            self.captureComplete.emit(image)

        else:
            self.captureComplete.emit(False)
    
    ## sendFirstMessage
    #
    # Kick off communication by sending the first message in the
    # queue, but only if we are not already waiting for messages
    # from HAL.
    #
    @hdebug.debug
    def sendFirstMessage(self):
        if not self.waiting_for_response:
            self.waiting_for_response = True
            self.tcp_client.sendMessage(self.messages.pop(0))
        
    ## setDirectory
    #
    # Sets self.directory to directory.
    #
    # @param directory The new working directory (as a string).
    #
    # @return True/False if starting capture was successful.
    #
    @hdebug.debug
    def setDirectory(self, directory):
        self.directory = directory

        if not self.tcp_client.isConnected():
            hdebug.logText("setDirectory: not connected to HAL.")
            return False

        self.messages.append(directoryMessage(self.directory))
        self.sendFirstMessage()
        return True

    ## shutDown
    #
    # Close the TCP/IP connection, if it is still open.
    #
    @hdebug.debug
    def shutDown(self):
        if self.tcp_client.isConnected():
            self.commDisconnect()

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

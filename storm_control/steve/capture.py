#!/usr/bin/env python
"""
Handles telling the acquisition program to get
a picture & converts the captured image into a
QPixmap.

Hazen 03/14
"""
import contextlib
import math
import numpy
import os
import time

from PyQt5 import QtCore, QtGui

# Debugging
import storm_control.sc_library.hdebug as hdebug

# Communication with the acquisition software
import storm_control.sc_library.tcpClient as tcpClient
import storm_control.sc_library.tcpMessage as tcpMessage

# Reading DAX files
import storm_control.sc_library.datareader as datareader

import storm_control.steve.coord as coord
import storm_control.steve.mosaicDialog as mosaicDialog


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

## mosaicSettingsMessage
#
# Creates a mosaic message for communication via TCPClient.
#
def mosaicSettingsMessage():
    return tcpMessage.TCPMessage(message_type = "Get Mosaic Settings")
    

def movieMessage(filename, directory):
    """
    Creates a movie message for communication via TCPClient.

    filename - The name of the movie.
    directory - Where to save the movie.
    """
    #
    # Note - We don't use 'overwrite' = True as the captureStart() method
    #        is supposed to take care of removing the previous film.
    #
    return tcpMessage.TCPMessage(message_type = "Take Movie",
                                 message_data = {"name" : filename,
                                                 "directory" : directory,
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
def moveStageMessage(stagex, stagey, is_other = False):  
    return tcpMessage.TCPMessage(message_type = "Move Stage",
                                 message_data = {"stage_x":stagex,
                                                 "stage_y":stagey,
                                                 "is_other":is_other})

## objectiveMessage
#
# Creates a objective message for communication via TCPClient.
#
def objectiveMessage(is_other = False):
    return tcpMessage.TCPMessage(message_type = "Get Objective",
                                 message_data = {"is_other":is_other})


## Image
#
# Image class for temporary storage of image data.
#
class Image(object):

    ## __init__
    #
    # @param data The image data (a numpy array).
    # @param size [image width, image height, number of frames].
    # @param params A StormXMLObject describing the acqusition.
    #
    def __init__(self, data, size, params):
        self.camera = params.get("acquisition.camera", "camera1")
        self.data = data
        self.height = size[0]

        # Pre HAL2 movies.
        if params.has(self.camera + ".scalemin"):
            self.image_min = params.get(self.camera + ".scalemin")
            self.image_max = params.get(self.camera + ".scalemax")
        else:
            self.image_min = params.get("display00.camera1.display_min")
            self.image_max = params.get("display00.camera1.display_max")
            
        self.parameters = params
        self.parameters_file = params.get("parameters_file", "NA")
        self.width = size[1]

        location = list(map(float, params.get("acquisition.stage_position").split(",")))
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
# movie (or movies), move to a position, etc.). This is done for user
# convenience because when the connection is active some features of
# HAL, such as movie acquisition, are locked out.
#
class Capture(QtCore.QObject):
    captureComplete = QtCore.pyqtSignal(object)
    changeObjective = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal()
    getPositionComplete = QtCore.pyqtSignal(object)
    newObjectiveData = QtCore.pyqtSignal(object)
    otherComplete = QtCore.pyqtSignal()

    ## __init__
    #
    # @param parameters A parameters xml object.
    #
    @hdebug.debug
    def __init__(self, parameters):
        QtCore.QObject.__init__(self)
        self.curr_objective = None
        self.curr_x = 0.0
        self.curr_y = 0.0
        self.directory = parameters.get("directory")
        self.fake_got_settings = False
        self.fake_objective = 1
        self.filename = parameters.get("image_filename")
        self.goto = False
        self.got_settings = False
        self.messages = []
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
        print("captureDone")
        
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
        print("captureStart", stagex, stagey)
        
        with contextlib.suppress(FileNotFoundError):
            os.remove(self.fullname())
            os.remove(self.fullname(extension = ".xml"))
        
        if not self.tcp_client.isConnected():
            hdebug.logText("captureStart: not connected to HAL.")
            return False

        if not self.got_settings:
            self.messages.append(mosaicSettingsMessage())                                 
        self.messages.append(objectiveMessage())
        self.messages.append(moveStageMessage(stagex, stagey))
        self.messages.append(movieMessage(self.filename,
                                          self.directory))
        self.sendFirstMessage()
        return True

    ## commConnect
    #
    # Initiate communication with HAL.
    #
    @hdebug.debug
    def commConnect(self):
        print("connect")
        self.tcp_client.startCommunication()

    ## commDisconnect
    #
    # Stop communication with HAL.
    #
    @hdebug.debug
    def commDisconnect(self):
        print("disconnect")
        self.tcp_client.stopCommunication()

    ## fullname
    #
    # returns the filename with path & extension.
    #
    # @return The filename with path & extension as a string.
    #
    @hdebug.debug
    def fullname(self, extension = ".dax"):
        return self.directory + self.filename + extension

    ## getObjective
    #
    # Called to query HAL about the current objective.
    #
    @hdebug.debug
    def getObjective(self):
        
        if not self.tcp_client.isConnected():
            hdebug.logText("getSettings: not connected to HAL.")
            return

        if not self.got_settings:
            self.messages.append(mosaicSettingsMessage())
        self.messages.append(objectiveMessage(True))
        self.sendFirstMessage()
        
    ## getPosition
    #
    # Called to query HAL about the current stage position.
    #
    @hdebug.debug
    def getPosition(self):

        if not self.tcp_client.isConnected():
            hdebug.logText("getPosition: not connected to HAL.")
            return

        if not self.got_settings:
            self.messages.append(mosaicSettingsMessage())
        self.messages.append(objectiveMessage())
        self.messages.append(getPositionMessage())
        self.sendFirstMessage()

    ## getSettings
    #
    # Try and get mosaic settings from HAL.
    #
    @hdebug.debug
    def getSettings(self):
        
        if not self.tcp_client.isConnected():
            hdebug.logText("getSettings: not connected to HAL.")
            return

        self.messages.append(mosaicSettingsMessage())
        self.messages.append(objectiveMessage(True))
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

        if not self.got_settings:
            self.messages.append(mosaicSettingsMessage())                                 
        self.messages.append(objectiveMessage())
        self.messages.append(moveStageMessage(stagex, stagey, True))
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

        #
        # If the message does not involve taking a movie and there are no more
        # messages then emit the otherComplete signal.
        #
        if (message.getData("is_other") == True) and (len(self.messages) == 0):
            self.otherComplete.emit()
            
        if (message.getType() == "Get Mosaic Settings"):
            self.got_settings = True
            #coord.Point.pixels_to_um = message.getResponse("pixels_to_um")
            i = 1
            while message.getResponse("obj" + str(i)) is not None:
                self.newObjectiveData.emit(message.getResponse("obj" + str(i)).split(","))
                i += 1
            
        if (message.getType() == "Get Objective"):
            if self.curr_objective is None or (self.curr_objective != message.getResponse("objective")):
                self.curr_objective = message.getResponse("objective")
                self.changeObjective.emit(self.curr_objective)

        if (message.getType() == "Get Stage Position"):
            a_point = coord.Point(message.getResponse("stage_x"),
                                  message.getResponse("stage_y"),
                                  "um")
            self.getPositionComplete.emit(a_point)

        #
        # self.loadImage() will emit the captureComplete signal.
        #
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
    def loadImage(self, filename, frame_num = 0):
        success = False

        # Deals with a file system race condition?
        # Or is it a acquisition software problem?
        time.sleep(0.05)
        tries = 0
        while (not success) and (tries < 4):
            try:
                movie = datareader.reader(filename)
                frame = movie.loadAFrame(frame_num)
                movie.closeFilePtr()
                success = True

            except IOError:
                print("Failed to load:" + filename + " frame " + str(frame_num))
                frame = None
                time.sleep(0.05)
            tries += 1

        if type(frame) == type(numpy.array([])):

            #
            # Check if the movie contains all the XML or if the XML is
            # just faked, for example by generating it from a .inf file.
            #
            if movie.xml.get("faked_xml", False):
                
                # Prompt user for settings for the first film.
                if not self.fake_got_settings:
                    settings = mosaicDialog.execMosaicDialog()
                    self.newObjectiveData.emit(settings[4:])
                    self.fake_got_settings = True
                    self.fake_objective += 1

                obj_name = "obj" + str(self.fake_objective)
                settings = mosaicDialog.getMosaicSettings()
                
                movie.xml.set("mosaic." + obj_name, ",".join(map(str, settings[4:])))
                movie.xml.set("mosaic.objective", obj_name)
                movie.xml.set("mosaic.flip_horizontal", settings[0])
                movie.xml.set("mosaic.flip_vertical", settings[1])
                movie.xml.set("mosaic.transpose", settings[2])

            else:
                
                #
                # If we are working off-line we might need to load the mosaic
                # settings first.
                #
                if not self.got_settings:
                    i = 1
                    while movie.xml.has("mosaic.obj" + str(i)):
                        obj_data = movie.xml.get("mosaic.obj" + str(i))
                        self.newObjectiveData.emit(obj_data.split(","))
                        i += 1
                        
            if movie.xml.get("mosaic.flip_horizontal", False):
                frame = numpy.fliplr(frame)
            if movie.xml.get("mosaic.flip_vertical", False):
                frame = numpy.flipud(frame)
            if movie.xml.get("mosaic.transpose", False):
                frame = numpy.transpose(frame)
            image = Image(frame,
                          movie.filmSize(),
                          movie.filmParameters())

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

        #if not self.tcp_client.isConnected():
        #    hdebug.logText("setDirectory: not connected to HAL.")
        #    return False

        #self.messages.append(directoryMessage(self.directory))
        #self.sendFirstMessage()
        #return True

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

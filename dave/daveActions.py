#!/usr/bin/python
#
## @file
#
# Collection of classes that control the establish the basic operation of dave
# as it issues various types of commands to HAL and Kilroy
#
# Jeff 3/14 
#

import sc_library.tcpMessage as tcpMessage
from PyQt4 import QtCore

## DaveAction
#
# The base class for a dave action.
#
class DaveAction(QtCore.QObject):

    # Define custom signal
    complete_signal = QtCore.pyqtSignal(object)
    error_signal = QtCore.pyqtSignal(object)
    
    ## __init__
    #
    # Default initialization.
    #
    # @param tcp_client A tcp communications object
    # @param parent A parent class
    #
    def __init__(self, tcp_client, parent = None):

        # Initialize parent class
        QtCore.QObject.__init__(self, parent)

        self.tcp_client = tcp_client
        self.message = None

        # Define pause behaviors
        self.should_pause = False # Pause after completion
        self.should_pause_after_error = True # Pause after error

        # Initialize internal timer
        self.lost_message_timer = QtCore.QTimer(self)
        self.lost_message_timer.setSingleShot(True)
        self.lost_message_timer.timeout.connect(self.handleTimerDone)
        self.lost_message_delay = 2000 # Wait for a test message to be returned before issuing an error

    ## abort
    #
    # Handle an external abort call
    #
    def abort(self):
        self.completeAction(self.message)

    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        self.tcp_client.messageReceived.disconnect()

    ## completeAction
    #
    # Handle the completion of an action
    #
    # @param message A TCP message object
    #
    def completeAction(self, message):
        self.complete_signal.emit(message)
    
    ## completeActionWithError
    #
    # Send an error message if needed
    #
    # @param message A TCP message object
    #
    def completeActionWithError(self, message):
        if self.should_pause_after_error == True:
            self.should_pause = True
        self.error_signal.emit(message)

    ## handleReply
    #
    # handle the return of a message
    #
    # @param message A TCP message object
    #
    def handleReply(self, message):
        # Stop lost message timer
        self.lost_message_timer.stop()
        # Check to see if the same message got returned
        if not (message.getID() == self.message.getID()):
            message.setError(True, "Communication Error: Incorrect Message Returned")
            self.completeActionWithError(message)
        elif message.hasError():
            self.completeActionWithError(message)
        else: # Correct message and no error
            self.completeAction(message)

    ## handleTimerDone
    #
    # Handle a timer done signal
    #
    def handleTimerDone(self):
        error_str = "A message of type " + self.message.getType() + " was never received.\n"
        error_str += "Perhaps a module is missing?"
        self.message.setError(True, error_str)
        self.completeActionWithError(self.message)

    ## setTest
    #
    # Converts the Dave Action to a test request
    #
    def setTest(self, boolean):
        self.message.test = boolean

    ## shouldPause
    #
    # Determine if the command engine should pause after this action
    #
    # @return A boolean determining if the program pauses after this action is complete
    def shouldPause(self):
        return self.should_pause

    ## start
    #
    # Start the action.
    #
    def start(self):
        self.tcp_client.messageReceived.connect(self.handleReply)
        if self.message.isTest():
            self.lost_message_timer.start(self.lost_message_delay)
        self.tcp_client.sendMessage(self.message)

# 
# Specific Actions
# 

## DaveActionValveProtocol
#
# The fluidics protocol action. Send commands to Kilroy.
#
class DaveActionValveProtocol(DaveAction):

    ## __init__
    #
    # Initialize the valve protocol action
    #
    # @param tcp_client A tcp communications object.
    # @param protocols A valve protocols xml object
    #
    def __init__(self, tcp_client, protocol_xml):
        DaveAction.__init__(self, tcp_client)
        self.protocol_name = protocol_xml.protocol_name
        self.protocol_is_running = False

        self.message = tcpMessage.TCPMessage(message_type = "Kilroy Protocol",
                                             message_data = {"name": self.protocol_name})

## DaveDelay
#
# This action introduces a defined delay in a dave action.  
#
class DaveDelay(DaveAction):
    ## __init__
    #
    # @param tcp_client A tcp communications object.
    #
    def __init__(self, delay):
        # Initialize parent class with no tcp_client
        DaveAction.__init__(self, None)
    
        # Prepare delay timer
        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.handleTimerComplete)
        self.delay = delay
        
        # Create message and add delay time for accurate dave time estimates
        self.message = tcpMessage.TCPMessage(message_type = "Delay",
                                             message_data = {"delay", self.delay});
        self.message.addResponse("duration", self.delay)

    ## abort
    #
    # Handle an external abort call
    #
    def abort(self):
        self.delay_timer.stop()
        self.completeAction(self.message)

    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        pass

    ## handleTimerComplete
    #
    # Handle completion of the felay timer
    #
    def handleTimerComplete(self):
        self.completeAction(self.message)

    ## start
    #
    # Start the action.
    #
    def start(self):
        if self.message.isTest():
            self.completeAction(self.message)
        else:
            self.delay_timer.start(self.delay)
            print "Delaying " + str(self.delay) + " ms"

## FindSum
#
# The find sum action.
#
class FindSum(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object
    # @param min_sum The minimum sum that we should get from HAL upon completion of this action.
    #
    def __init__(self, tcp_client, min_sum):
        DaveAction.__init__(self, tcp_client)
        self.min_sum = min_sum
        self.message = tcpMessage.TCPMessage(message_type = "Find Sum",
                                             message_data = {"min_sum": min_sum})

    ## handleReply
    #
    # Overload of default handleReply to allow comparison of min_sum
    #
    # @param message A TCP message object
    #
    def handleReply(self, message):
        found_sum = message.getResponse("found_sum")
        if not (found_sum == None) and (found_sum <= self.min_sum):
            message.setError(True, "Found sum " + str(found_sum) + " is smaller than minimum sum " + str(self.min_sum))
        DaveAction.handleReply(self, message)

## MoveStage
#
# The movie parameters action.
#
class MoveStage(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object.
    # @param command A XML command object for a movie.
    #
    def __init__(self, tcp_client, command):
        DaveAction.__init__(self, tcp_client)
        self.message = tcpMessage.TCPMessage(message_type = "Move Stage",
                                             message_data = {"stage_x":command.stage_x,
                                                             "stage_y":command.stage_y})
## RecenterPiezo
#
# The piezo recentering action. Note that this is only useful if the microscope
# has a motorized Z.
#
class RecenterPiezo(DaveAction):
    ## __init__
    #
    # @param tcp_client A tcp communications object.
    #
    def __init__(self, tcp_client):
        DaveAction.__init__(self, tcp_client)
        self.message = tcpMessage.TCPMessage(message_type = "Recenter Piezo")

## SetDirectory
#
# Change the Hal Directory.
#
class SetDirectory(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object
    # @param directory The desired directory.
    #
    def __init__(self, tcp_client, directory):
        DaveAction.__init__(self, tcp_client)
        self.message = tcpMessage.TCPMessage(message_type = "Set Directory",
                                             message_data = {"directory": directory})

## Set Focus Lock Target
#
# The set focus lock target action.
#
class SetFocusLockTarget(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object
    # @param lock_target The target for the focus lock.
    #
    def __init__(self, tcp_client, lock_target):
        DaveAction.__init__(self, tcp_client)
        self.message = tcpMessage.TCPMessage(message_type = "Set Lock Target",
                                             message_data = {"lock_target": lock_target})

## Set Parameters
#
# The action responsible for setting the movie parameters in Hal.
#
class SetParameters(DaveAction):
    ## __init__
    #
    # @param tcp_client A tcp communications object.    
    # @param command A XML command object for a movie.
    #
    def __init__(self, tcp_client, command):
        DaveAction.__init__(self, tcp_client)
        self.message = tcpMessage.TCPMessage(message_type = "Set Parameters",
                                             message_data = {"parameters": command.parameters})

## SetProgression
#
# The action responsible for setting the illumination progression.
#
class SetProgression(DaveAction):
    ## __init__
    #
    # @param tcp_client A tcp communications object.    
    # @param progression an XML object describing the desired progression
    #
    def __init__(self, tcp_client, progression):
        DaveAction.__init__(self, tcp_client)
        message_data = {"type":progression.type}
        if hasattr(progression, "filename"):
            message_data["filename"] = progression.filename
        if progression.channels:
            message_data["channels"] = progression.channels
        
        self.message = tcpMessage.TCPMessage(message_type = "Set Progression",
                                             message_data = message_data)

## TakeMovie
#
# Send a take movie command to Hal
#
class TakeMovie(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object.
    # @param command A XML command object for a movie.
    #
    def __init__(self, tcp_client, command):
        DaveAction.__init__(self, tcp_client)
        message_data = {"name":command.name,
                        "length":command.length,
                        "min_spots":command.min_spots}
        if hasattr(command, "parameters"):
            message_data["parameters"] = command.parameters
        else:
            message_data["parameters"] = None
        if hasattr(command, "directory"):
            message_data["directory"] = command.directory
        if hasattr(command, "overwrite"):
            message_data["overwrite"] = command.overwrite

        self.min_spots = command.min_spots
        self.message = tcpMessage.TCPMessage(message_type = "Take Movie",
                                             message_data = message_data)

    ## abort
    #
    # Send an abort message to Hal
    #
    def abort(self):
        stop_message = tcpMessage.TCPMessage(message_type = "Abort Movie")
        self.tcp_client.sendMessage(stop_message)

    ## handleReply
    #
    # Overload of default handleReply to allow comparison of min_spots
    #
    # @param message A TCP message object
    #
    def handleReply(self, message):
        found_spots = message.getResponse("found_spots")
        if not (found_spots == None) and (found_spots < self.min_spots):
            err_str = str(found_spots) + " found molecules is less than the target: "
            err_str += str(self.min_spots)
            message.setError(True, err_str)
        DaveAction.handleReply(self,message)                

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

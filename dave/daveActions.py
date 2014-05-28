#!/usr/bin/python
#
## @file
#
# Collection of classes that control the establish the basic operation of dave
# as it issues various types of commands to HAL and Kilroy
#
# Jeff 3/14 
#
# Hazen 05/14
#

from xml.etree import ElementTree
from PyQt4 import QtCore

import sc_library.tcpMessage as tcpMessage


## addField
#
# @param block A ElementTree node.
# @param name The name of the field as a string.
# @param value The value of the field.
#
def addField(block, name, value):
    field = ElementTree.SubElement(block, name)
    field.set("type", str(type(value).__name__))
    field.text = str(value)


## DaveAction
#
# The base class for a dave action (DA for short).
#
class DaveAction(QtCore.QObject):

    # Define custom signal
    complete_signal = QtCore.pyqtSignal(object)
    error_signal = QtCore.pyqtSignal(object)
    
    ## __init__
    #
    # Default initialization.
    #
    def __init__(self):

        # Initialize parent class
        QtCore.QObject.__init__(self, None)

        self.action_type = "NA"
        self.disk_usage = 0
        self.duration = 0
        self.tcp_client = None
        self.message = None
        self.valid = True

        # Define pause behaviors
        self.should_pause = False            # Pause after completion
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

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        pass

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
        if message.isTest():
            time = message.getResponse("duration")
            if time is not None: self.duration = time
            space = message.getResponse("disk_usage")
            if space is not None: self.disk_usage = space
        self.complete_signal.emit(message)

    ## completeActionWithError
    #
    # Send an error message if needed
    #
    # @param message A TCP message object
    #
    def completeActionWithError(self, message):
        if (self.should_pause_after_error == True):
            self.should_pause = True
        self.error_signal.emit(message)

    ## getActionType
    #
    # @return The type of the action (i.e. "hal", "kilroy", ..)
    #
    def getActionType(self):
        return self.action_type

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return type(self).__name__[2:]

    ## getDuration
    #
    # @return Duration (in seconds?)
    #
    def getDuration(self):
        return self.duration

    ## getLongDescriptor
    #
    # @return A (long) string that describes the action.
    #
    def getLongDescriptor(self):
        return self.getDescriptor()

    ## getUsage
    #
    # @return Disk usage.
    #
    def getUsage(self):
        return self.disk_usage

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

    ## isValid
    #
    # @return True/False is the command is valid.
    #
    def isValid(self):
        return self.valid

    ## setProperty
    #
    # Set object property, throw an error if the property is not recognized.
    #
    def setProperty(self, pname, pvalue):
        if pname in self.properties.keys():
            self.properties[pname] = pvalue
        else:
            raise Exception(pname + " is not a valid property for " + str(type(self)))

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        pass

    ## setValid
    #
    # @param is_valid True/False is this message is valid.
    #
    def setValid(self, is_valid):
        self.valid = is_valid

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
    # @param tcp_client The TCP client to use for communication.
    # @param test_mode Send the command in test mode.
    #
    def start(self, tcp_client, test_mode):
        self.tcp_client = tcp_client
        self.message.setTestMode(test_mode)

        self.tcp_client.messageReceived.connect(self.handleReply)
        if self.message.isTest():
            self.lost_message_timer.start(self.lost_message_delay)
        self.tcp_client.sendMessage(self.message)


# 
# Specific Actions
# 

## DADelay
#
# This action introduces a defined delay in a dave action.  
#
class DADelay(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)
    
    ## abort
    #
    # Handle an external abort call
    #
    def abort(self):
        self.delay_timer.stop()
        self.completeAction(self.message)

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):

        # Determine delays.
        base_delay = node.find("base_delay")
        if base_delay is not None:
            base_delay = int(base_delay.text)
        else:
            base_delay = 0

        delay = node.find("delay")
        if delay is not None:
            delay = int(delay.text)
        else:
            delay = 0

        # Add action if total delay is greater than zero.
        total_delay = base_delay + delay
        if (total_delay > 0):
            block = ElementTree.SubElement(etree, str(type(self).__name__)),
            addField(block, "delay", total_delay)

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

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):

        # Prepare delay timer
        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.handleTimerComplete)
        self.delay = int(node.find("delay").text)
        
        # Create message and add delay time for accurate dave time estimates
        self.message = tcpMessage.TCPMessage(message_type = "Delay",
                                             message_data = {"delay", self.delay});
        self.message.addResponse("duration", self.delay)

    ## start
    #
    # Start the action.
    #
    # @param dummy Ignored.
    # @param test_mode Send the command in test mode.
    #
    def start(self, dummy, test_mode):
        self.message.setTestMode(test_mode)

        if self.message.isTest():
            self.completeAction(self.message)
        else:
            self.delay_timer.start(self.delay)
            print "Delaying " + str(self.delay) + " ms"

## DAFindSum
#
# The find sum action.
#
class DAFindSum(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        find_sum = node.find("find_sum")
        if (find_sum is not None):
            min_sum = float(find_sum.text)
            if (min_sum > 0.0):
                block = ElementTree.SubElement(etree, str(type(self).__name__))
                addField(block, "min_sum", min_sum)
                
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

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.min_sum = int(node.find("min_sum").text)
        self.message = tcpMessage.TCPMessage(message_type = "Find Sum",
                                             message_data = {"min_sum": self.min_sum})

## DAMoveStage
#
# The movie parameters action.
#
class DAMoveStage(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object.
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        stage_x = node.find("stage_x")
        stage_y = node.find("stage_y")
        if (stage_x is not None) and (stage_y is not None):
            block = ElementTree.SubElement(etree, str(type(self).__name__))
            addField(block, "stage_x", float(stage_x.text))
            addField(block, "stage_y", float(stage_y.text))

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.message = tcpMessage.TCPMessage(message_type = "Move Stage",
                                             message_data = {"stage_x" : float(node.find("stage_x").text),
                                                             "stage_y" : float(node.find("stage_y").text)})


class DAPause(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object.
    #
    def __init__(self):
        DaveAction.__init__(self)

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        first_movie = node.find("first_movie")
        pause = node.find("pause")
        if (first_movie is not None) or (pause is not None):
            block = ElementTree.SubElement(etree, str(type(self).__name__))
        
    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        pass

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        # Create message and add delay time for accurate dave time estimates
        self.message = tcpMessage.TCPMessage(message_type = "Pause");
        
        # Define pause behaviors
        self.should_pause = True

    ## start
    #
    # Start the action.
    #
    # @param dummy Ignored.
    # @param test_mode Send the command in test mode.
    #
    def start(self, dummy, test_mode):
        self.message.setTestMode(test_mode)

        if self.message.isTest():
            self.completeAction(self.message)
        else:
            self.completeAction(self.message)

## DARecenterPiezo
#
# The piezo recentering action. Note that this is only useful if the microscope
# has a motorized Z.
#
class DARecenterPiezo(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        recenter = node.find("recenter")
        if (recenter is not None):
            block = ElementTree.SubElement(etree, str(type(self).__name__))

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.message = tcpMessage.TCPMessage(message_type = "Recenter Piezo")

## DASetDirectory
#
# Change the Hal Directory.
#
class DASetDirectory(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        directory = node.find("directory")
        if (directory is not None):
            block = ElementTree.SubElement(etree, str(type(self).__name__))
            addField(block, "directory", directory.text)

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.message = tcpMessage.TCPMessage(message_type = "Set Directory",
                                             message_data = {"directory" : node.find("directory").text})

## DASetFocusLockTarget
#
# The set focus lock target action.
#
class DASetFocusLockTarget(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        lock_target = node.find("lock_target")
        if (lock_target is not None):
            block = ElementTree.SubElement(etree, str(type(self).__name__))
            addField(block, "lock_target", float(lock_target.text))

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.message = tcpMessage.TCPMessage(message_type = "Set Lock Target",
                                             message_data = {"lock_target" : float(node.find("lock_target").text)})

## DASetParameters
#
# The action responsible for setting the movie parameters in Hal.
#
class DASetParameters(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        parameters = node.find("parameters")
        if (parameters is not None):
            block = ElementTree.SubElement(etree, str(type(self).__name__))
            addField(block, "parameters", float(parameters.text))

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.message = tcpMessage.TCPMessage(message_type = "Set Parameters",
                                             message_data = {"parameters" : node.find("parameters").text})

## DASetProgression
#
# The action responsible for setting the illumination progression.
#
class DASetProgression(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        progression = node.find("progression")
        if progression is not None:
            node.append(progression)

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        pass
#        message_data = {"type":progression.type}
#        if hasattr(progression, "filename"):
#            message_data["filename"] = progression.filename
#        if progression.channels:
#            message_data["channels"] = progression.channels
#        
#        self.message = tcpMessage.TCPMessage(message_type = "Set Progression",
#                                             message_data = message_data)

## DATakeMovie
#
# Send a take movie command to Hal
#
class DATakeMovie(DaveAction):

    ## __init__
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"
        self.properties = {"name" : None,
                           "length" : None,
                           "min_spots" : None,
                           "parameters" : None,
                           "directory" : None,
                           "overwrite" : None}

    ## abort
    #
    # Send an abort message to Hal
    #
    def abort(self):
        stop_message = tcpMessage.TCPMessage(message_type = "Abort Movie")
        self.tcp_client.sendMessage(stop_message)

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        name = node.find("name")
        length = node.find("length")
        min_spots = node.find("min_spots")
        parameters = node.find("parameters")
        directory = node.find("directory")
        overwrite = node.find("overwrite")
        if (name is not None) and (length is not None):
            length = int(length.text)
            if (length > 0):
                block = ElementTree.SubElement(etree, str(type(self).__name__))
                addField(block, "name", name.text)
                addField(block, "length", length)

                if min_spots is not None:
                    addField(block, "min_spots", int(min_spots.txt)

                if parameters is not None:
                    addField(block, "parameters", parameters.text)

                if directory is not None:
                    addField(block, "directory", directory.text)

                if overwrite is not None:
                    addField(block, "overwrite", overwrite.text)

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

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.min_spots = 0
        if node.find("min_spots") is not None:
            self.min_spots = int(node.find("min_spots").text)
            
        message_data = {"name" : node.find("name").text,
                        "length" : int(node.find("length").text),
                        "min_spots" : self.min_spots,
                        "parameters" : None}
        
        if node.find("parameters") is not None:
            message_data["parameters"] = node.find("parameters").text
            
        if node.find("directory") is not None:
            message_data["directory"] = node.find("directory").text
            
        if node.find("overwrite") is not None:
            message_data["overwrite"] = node.find("overwrite").text

        self.message = tcpMessage.TCPMessage(message_type = "Take Movie",
                                             message_data = message_data)


## DAValveProtocol
#
# The fluidics protocol action. Send commands to Kilroy.
#
class DAValveProtocol(DaveAction):

    ## __init__
    #
    # Initialize the valve protocol action
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "kilroy"
        self.properties = {"name" : None}

    ## addToETree
    #
    # Save the information necessary to recreate the action to a XML ElementTree.
    #
    # @param etree The XML ElementTree to add to.
    # @param node The XML node to parse what to add.
    #
    def addToETree(self, etree, node):
        
        # This overlaps with movie..
        name = node.find("name")
        if (name is not None):
            block = ElementTree.SubElement(etree, str(type(self).__name__))
            addField(block, "name", name.text)

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.protocol_name = node.find("name").text
        self.protocol_is_running = False

        self.message = tcpMessage.TCPMessage(message_type = "Kilroy Protocol",
                                             message_data = {"name": self.protocol_name})

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

#!/usr/bin/python
#
## @file
#
# Collection of classes that control the establish the basic operation of dave
# as it issues various types of commands to HAL and Kilroy
#
# Jeff 3/14 
#
# Hazen 09/14
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
        self.id = None
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

    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        self.tcp_client.messageReceived.disconnect()

    ## createETree
    #
    # Takes a dictionary that may (or may not) contain the information that is
    # is necessary to create the Action. If the information is not present then
    # None is returned. If the information is present then a ElementTree is
    # is returned containing the information necessary to create the Action.
    #
    # @param dict A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        pass

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

    ## getID
    #
    # @return An ID used to identify 'unique' actions for validation
    #
    def getID(self):
        return self.id

    ## getLongDescriptor
    #
    # @return A N x 2 array containing the message data.
    #
    def getLongDescriptor(self):
        if self.message is not None:
            mdict = self.message.getMessageData()
            data = []
            for key in sorted(mdict):
                data.append([key, mdict[key]])

            # Add disk usage and duration
            if not (self.disk_usage == 0):
                data.append(["disk usage (kb)", self.disk_usage])
            if not (self.duration == 0):
                data.append(["duration (s)", self.duration])
            
            return data
        else:
            return [None,None]

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

    ## setDuration
    #
    # @param duration The estimated time to execute.
    #
    def setDuration(self, duration):
        self.duration = duration

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        pass

    ## setDiskUsage
    #
    # @param disk_usage The disk usage.
    #
    def setDiskUsage(self, disk_usage):
        self.disk_usage = disk_usage

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
# This action introduces a defined delay.
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

    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        pass

    ## createETree
    #
    # @param dict A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        delay = dictionary.get("delay")
        if delay is not None:
            block = ElementTree.Element(str(type(self).__name__))
            addField(block, "delay", delay)
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "pause for " + str(self.delay) + "ms"

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
                                             message_data = {"delay": self.delay});
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

    ## createETree
    #
    # @param dict A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        find_sum = dictionary.get("find_sum")
        if find_sum is None:
            return

        if (find_sum > 0.0):
            block = ElementTree.Element(str(type(self).__name__))
            addField(block, "min_sum", find_sum)
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "find sum (minimum sum = " + str(self.min_sum) + ")"
                
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
        self.min_sum = float(node.find("min_sum").text)
        self.message = tcpMessage.TCPMessage(message_type = "Find Sum",
                                             message_data = {"min_sum": self.min_sum})


## DAMoveStage
#
# The move stage action.
#
class DAMoveStage(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object.
    #
    def __init__(self):
        DaveAction.__init__(self)

        self.action_type = "hal"

    ## createETree
    #
    # @param dict A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        stage_x = dictionary.get("stage_x")
        stage_y = dictionary.get("stage_y")
        if (stage_x is not None) and (stage_y is not None):
            block = ElementTree.Element(str(type(self).__name__))
            addField(block, "stage_x", stage_x)
            addField(block, "stage_y", stage_y)
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "move stage to " + str(self.stage_x) + ", " + str(self.stage_y)

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.stage_x = float(node.find("stage_x").text)
        self.stage_y = float(node.find("stage_y").text)
        self.message = tcpMessage.TCPMessage(message_type = "Move Stage",
                                             message_data = {"stage_x" : self.stage_x,
                                                             "stage_y" : self.stage_y})

        # Create id to indicate required validation
        self.id = self.message.getType() + " "
        self.id += "stage_x: " + str(self.stage_x) + " "
        self.id += "stage_y: " + str(self.stage_y)

## DAPause
#
# This action causes Dave to pause.
#
class DAPause(DaveAction):

    ## __init__
    #
    # @param tcp_client A tcp communications object.
    #
    def __init__(self):
        DaveAction.__init__(self)

    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        pass

    ## createETree
    #
    # @param dict A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        pause = dictionary.get("pause")
        if (pause is not None):
            block = ElementTree.Element(str(type(self).__name__))
            return block
        
    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "pause"

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

    ## createETree
    #
    # @param dictionary A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        recenter = dictionary.get("recenter")
        if (recenter is not None):
            block = ElementTree.Element(str(type(self).__name__))
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "recenter piezo"

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

    ## createETree
    #
    # @param dictionary A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        directory = dictionary.get("directory")
        if (directory is not None):
            block = ElementTree.Element(str(type(self).__name__))
            addField(block, "directory", directory)
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "change directory to " + self.directory

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.directory = node.find("directory").text
        self.message = tcpMessage.TCPMessage(message_type = "Set Directory",
                                             message_data = {"directory": self.directory})

        # Require validation
        self.id = self.message.getType() + " "
        self.id += self.directory

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

    ## createETree
    #
    # @param dictionary A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        lock_target = dictionary.get("lock_target")
        if (lock_target is not None):
            block = ElementTree.Element(str(type(self).__name__))
            addField(block, "lock_target", lock_target)
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "set focus lock target to " + str(self.lock_target)

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.lock_target = float(node.find("lock_target").text)
        self.message = tcpMessage.TCPMessage(message_type = "Set Lock Target",
                                             message_data = {"lock_target" : self.lock_target})


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

    ## createETree
    #
    # @param dictionary A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        parameters = dictionary.get("parameters")
        if (parameters is not None):
            block = ElementTree.Element(str(type(self).__name__))
            addField(block, "parameters", parameters)
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "set parameters to " + str(self.parameters)

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        p_node = node.find("parameters")
        if (p_node.attrib["type"] == "int"):
            self.parameters = int(node.find("parameters").text)
        else:
            self.parameters = node.find("parameters").text
        self.message = tcpMessage.TCPMessage(message_type = "Set Parameters",
                                             message_data = {"parameters" : self.parameters})

        # Require validation
        self.id = self.message.getType() + " "
        self.id += str(self.parameters)

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

    ## createETree
    #
    # @param dictionary A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        progression = dictionary.get("progression")
        if progression is not None:
            block = ElementTree.Element(str(type(self).__name__))
            for pnode in progression:
                # The round trip fixes some white space issues.
                block.append(ElementTree.fromstring(ElementTree.tostring(pnode)))
            return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "set progressions to " + self.type

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):

        self.type = node.find("type").text
        message_data = {"type" : self.type}

        # File progression.
        if node.find("filename") is not None:
            message_data["filename"] = node.find("filename").text

        # Math progression.
        elif node.find("channel") is not None:
            channels = []
            for ch_node in [x for x in node if (x.tag == "channel")]:
                channel = int(ch_node.text)
                start = float(ch_node.attrib["start"])

                if "frames" in ch_node.attrib:
                    frames = int(ch_node.attrib["frames"])
                else:
                    frames = 100

                if "inc" in ch_node.attrib:
                    inc = float(ch_node.attrib["inc"])
                else:
                    inc = 0.0
    
                channels.append([channel, start, frames, inc])

            message_data["channels"] = channels
        
        self.message = tcpMessage.TCPMessage(message_type = "Set Progression",
                                             message_data = message_data)

        # Require validation only for provided filenames
        if node.find("filename") is not None:
            self.id = self.message.getType() + " "
            self.id += node.find("filename").text   

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

    ## createETree
    #
    # @param dictionary A dictionary.
    #
    # @return A ElementTree object or None.
    #
    def createETree(self, dictionary):
        name = dictionary.get("name")
        length = dictionary.get("length")
        min_spots = dictionary.get("min_spots")
        parameters = dictionary.get("parameters")
        directory = dictionary.get("directory")
        overwrite = dictionary.get("overwrite")
        if (name is not None) and (length is not None):
            if (length > 0):
                block = ElementTree.Element(str(type(self).__name__))
                addField(block, "name", name)
                addField(block, "length", length)

                if min_spots is not None:
                    addField(block, "min_spots", min_spots)

                if parameters is not None:
                    addField(block, "parameters", parameters)

                if directory is not None:
                    addField(block, "directory", directory)

                if overwrite is not None:
                    addField(block, "overwrite", overwrite)

                return block

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        if (self.min_spots > 0):
            return "take movie " + self.name + ", " + str(self.length) + " frames, " + str(self.min_spots) + " minimum spots"
        else:
            return "take movie " + self.name + ", " + str(self.length) + " frames"

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
        self.name = node.find("name").text
        self.length = int(node.find("length").text)

        self.min_spots = 0
        if node.find("min_spots") is not None:
            self.min_spots = int(node.find("min_spots").text)
            
        message_data = {"name" : self.name,
                        "length" : self.length,
                        "min_spots" : self.min_spots,
                        "parameters" : None}
        
        if node.find("parameters") is not None:
            message_data["parameters"] = node.find("parameters").text
            
        if node.find("directory") is not None:
            message_data["directory"] = node.find("directory").text
            
        if node.find("overwrite") is not None:
            message_data["overwrite"] = True # Default is to overwrite
            
            boolean_text = node.find("overwrite").text
            if (boolean_text.lower() == "false"):
                message_data["overwrite"] = False

        self.message = tcpMessage.TCPMessage(message_type = "Take Movie",
                                             message_data = message_data)

        # Require validation
        self.id = self.message.getType() + " "
        self.id = str(self.length) + " "
        if message_data["parameters"] is not None:
            self.id = str(message_data["parameters"])

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

    ## createETree
    #
    # Generate a Element Tree for the valve protocol specified.
    #
    # @param dictionary A dictionary containing the relevant data to create the element tree
    #
    def createETree(self, dictionary):
        name = dictionary.get("name", None)
        if (name is not None):
            node = ElementTree.Element(str(type(self).__name__))
            node.text = name
            return node
        else:
            return None

    ## getDescriptor
    #
    # @return A string that describes the action.
    #
    def getDescriptor(self):
        return "valve protocol " + self.protocol_name

    ## setup
    #
    # Perform post creation initialization.
    #
    # @param node The node of an ElementTree.
    #
    def setup(self, node):
        self.protocol_name = node.text
        self.protocol_is_running = False

        self.message = tcpMessage.TCPMessage(message_type = "Kilroy Protocol",
                                             message_data = {"name": self.protocol_name})

        # Require validation
        self.id = self.message.getType() + " "
        self.id = self.protocol_name        

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

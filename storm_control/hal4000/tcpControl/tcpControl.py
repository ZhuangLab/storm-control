#!/usr/bin/env python
"""
Handles remote control (via TCP/IP of the data collection program).

Hazen 05/17
"""

import os
from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.tcpMessage as tcpMessage
import storm_control.sc_library.tcpServer as tcpServer

import storm_control.hal4000.film.filmRequest as filmRequest
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


def calculateMovieStats(tcp_message, parameters):
    """
    Calculate movie size and duration based on parameters
    """
    #
    # FIXME: Accuracy is not what it could be as we don't know how
    #        much space the feeds will take, if any.
    #
    # FIXME: We are assuming that the cameras are named camera1,
    #        camera2, etc..
    #

    def cameraName(i):
        return "camera" + str(i)

    frames = tcp_message.getData("length")
    
    # Estimate movie size in megabytes.
    total_bytes_per_frame = 0
    i = 1
    while parameters.has(cameraName(i)):
        if parameters.get(cameraName(i) + ".saved"):
            total_bytes_per_frame += parameters.get(cameraName(i) + ".bytes_per_frame")
            i += 1
    tcp_message.addResponse("disk_usage", (total_bytes_per_frame * frames)/(2**20))

    # Estimate movie duration in seconds.
    fps = parameters.get(parameters.get("timing.time_base") + ".fps")
    tcp_message.addResponse("duration", frames/fps)
    
    
class TCPAction(QtCore.QObject):
    """
    The base class for TCP messages that are handled using actions. These
    are pretty similar to testing actions.
    """
    actionMessage = QtCore.pyqtSignal(object)

    def __init__(self, tcp_message = None, **kwds):
        super().__init__(**kwds)
        self.hal_message = halMessage.HalMessage(m_type = "tcp message",
                                                 data = {"tcp message" : tcp_message})
        self.tcp_message = tcp_message
        self.was_handled = False

    def getData(self):
        """
        Get any data that the action may have acquired. If anything this
        is usually a storm XML parameters object.

        This is not the same as TCP message response data. 
        """
        return {}
    
    def getHalMessage(self):
        return self.hal_message

    def handleResponses(self, message):
        """
        Handles message responses as a halModule.HalModule would.

        Return True/False so that the TCPControl module will know if this action
        can be finalized.
        """
        if (message == self.hal_message):
            self.was_handled = message.hasResponses()
            return True
        else:
            return False

    def processMessage(self, message):
        """
        Processes message as a halModule.HalModule would.

        Return True/False so that the TCPControl module will know if this action
        can be finalized.
        """
        return False
        
    def sendResponse(self, server):
        if not self.was_handled:
            print(">> Warning no response to '" + self.tcp_message.getType() + "'")
            self.tcp_message.setError(True, "This message was not handled.")
        server.sendMessage(self.tcp_message)


class TCPActionGetMovieStats(TCPAction):
    """
    This is used to calculate the stats of a movie request that 
    included a parameters file.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.hal_message = halMessage.HalMessage(m_type = "get parameters",
                                                 data = {"index or name" : self.tcp_message.getData("parameters")})

    def handleResponses(self, message):

        # Check if this a response to our action, or a response to some
        # other message from the tcpControl class.
        if (message != self.hal_message):
            return False

        # Check for singleton response.
        responses = message.getResponses()
        assert (len(responses) == 1)

        # Check that the requested parameters were found.
        found = responses[0].getData()["found"]
        if not found:
            self.tcp_message.setError(True, "Parameters '" + self.tcp_message.getData("parameters") + "' not found")
            self.was_handled = True
            return True
        
        parameters = responses[0].getData()["parameters"]

        # Check if the parameters are initialized.
        if parameters.get("initialized", False):
            calculateMovieStats(self.tcp_message, parameters)
            self.was_handled = True
            return True
        else:
            msg = halMessage.HalMessage(m_type = "set parameters",
                                        data = {"index or name" : self.tcp_message.getData("parameters")})
            self.actionMessage.emit(msg)
            return False

    def processMessage(self, message):
        if message.isType("updated parameters"):
            parameters = message.getData()["parameters"]
            calculateMovieStats(self.tcp_message, parameters)
            self.was_handled = True
            return True
        return False

    
class TCPActionGetParameters(TCPAction):
    """
    This is used to get a particular set of parameters. If the parameters 
    that are returned have not been initialized then this will also 
    instruct settings.settings to switch to these parameters.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.hal_message = halMessage.HalMessage(m_type = "get parameters",
                                                 data = {"index or name" : self.tcp_message.getData("parameters")})
        self.parameters = None

    def getData(self):
        return {"parameters" : self.parameters}

    def handleResponses(self, message):

        # Check if this a response to our action, or a response to some
        # other message from the tcpControl class.
        if (message != self.hal_message):
            return False

        # Check for singleton response.
        responses = message.getResponses()
        assert (len(responses) == 1)

        # Check that the requested parameters were found.
        found = responses[0].getData()["found"]
        if not found:
            self.tcp_message.setError(True, "Parameters '" + self.tcp_message.getData("parameters") + "' not found")
            self.was_handled = True
            return True
        
        self.parameters = responses[0].getData()["parameters"]

        # Check if the parameters are initialized.
        if not self.parameters.get("initialized", False):
            msg = halMessage.HalMessage(m_type = "set parameters",
                                        data = {"index or name" : self.tcp_message.getData("parameters")})
            self.actionMessage.emit(msg)
            return False

        self.was_handled = True        
        return True

    def processMessage(self, message):
        if message.isType("updated parameters"):
            self.was_handled = True
            self.parameters = message.getData()["parameters"]
            return True
        return False


class TCPActionSetParameters(TCPAction):
    """
    This is used to tell HAL to use a particular set of parameters.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.hal_message = halMessage.HalMessage(m_type = "set parameters",
                                                 data = {"index or name" : self.tcp_message.getData("parameters")})
        self.parameters = None
        
    def getData(self):
        return {"parameters" : self.parameters}

    def handleResponses(self, message):
        
        # Check if this a response to our action, or a response to some
        # other message from the tcpControl class.
        if (message != self.hal_message):
            return False

        # Check for singleton response.
        responses = message.getResponses()
        assert (len(responses) == 1)

        # Check that the requested parameters were found.
        found = responses[0].getData()["found"]
        if not found:
            self.tcp_message.setError(True, "Parameters '" + self.tcp_message.getData("parameters") + "' not found")
            self.was_handled = True
            return True

        # Check if the requested parameters are the current parameters.
        if responses[0].getData()["current"]:
            self.was_handled = True
            return True
        
        return False

    def processMessage(self, message):
        if message.isType("updated parameters"):
            self.was_handled = True
            self.parameters = message.getData()["parameters"]
            return True
        return False


class TCPActionTakeMovie(TCPAction):
    """
    This is used to tell HAL to take a movie.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.was_handled = True
            
        self.film_request = filmRequest.FilmRequest(basename = self.tcp_message.getData("name"),
                                                    directory = self.tcp_message.getData("directory"),
                                                    frames = self.tcp_message.getData("length"),
                                                    overwrite = self.tcp_message.getData("overwrite", default = False),
                                                    tcp_request = True)

        # Do we need to change parameters first?
        if self.tcp_message.getData("parameters") is not None:
            self.hal_message = halMessage.HalMessage(m_type = "set parameters",
                                                     data = {"index or name" : self.tcp_message.getData("parameters")})

        # If not, just take the movie.
        else:
            self.hal_message = halMessage.HalMessage(m_type = "start film request",
                                                     data = {"request" : self.film_request})

    def handleResponses(self, message):
        #
        # This handles the case that the requested parameters are already
        # the current parameters.
        #

        # Check that this is a response to the 'set parameters' message.
        if not message.isType("set parameters"):
            return False
        
        # Check if this a response to our action, or a response to some
        # other message from the tcpControl class.
        if (message != self.hal_message):
            return False
        
        # Check for singleton response.
        responses = message.getResponses()
        assert (len(responses) == 1)

        # Check that the requested parameters were found.
        found = responses[0].getData()["found"]
        if not found:
            self.tcp_message.setError(True, "Parameters '" + self.tcp_message.getData("parameters") + "' not found")
            self.was_handled = True
            return True

        # If these are the current parameters, send a 'start film request', if
        # they are not then 'settings.settings' will switch HAL to these parameters
        # and we'll monitor for the completion of the parameter change.
        if responses[0].getData()["current"]:
            msg = halMessage.HalMessage(m_type = "start film request",
                                        data = {"request" : self.film_request})
            self.actionMessage.emit(msg)

        return False

    def processMessage(self, message):
        #
        # This is the signal that the parameter change is
        # complete and we can start filming.
        #
        if message.isType("changing parameters"):
            if not message.getData()["changing"]:
                msg = halMessage.HalMessage(m_type = "start film request",
                                            data = {"request" : self.film_request})
                self.actionMessage.emit(msg)

        #
        # The 'film lockout' message with data 'locked out' is the signal
        # that the film is complete.
        #
        elif message.isType("film lockout"):
            if not message.getData()["locked out"]:
                acq_p = message.getData()["acquisition parameters"]
                if acq_p.has("spot_counts"):
                    self.tcp_message.addResponse("found_spots", acq_p.get("spot_counts"))
                return True

        return False    

    
class Controller(QtCore.QObject):
    """
    This is the interface between HAL and a TCP client such as Dave. Most messages
    are simply wrapped and thrown into HAL's message queue, but some require 
    special processing.

    TCPActions are blocking, i.e. we won't send a response back to the TCP client 
    until they are processed.

    Actions are used for all TCP messages if they are testing, as the response is
    important.

    In parallel mode only the following TCP messages are handled as actions:
    1. 'Check Focus Lock'
    2. 'Find Sum'
    3. 'Set Parameters'
    4. 'Take Movie'

    The recommended order of TCP messages for maximum throughput in a standard 
    imaging cycle is:
    1. 'Move Stage'
    2. 'Set Parameters'
    3. 'Check Focus Lock'
    4. 'Take Movie'
    In this sequence 1 and 2 can happen in parallel.

    Note also the expectation that the TCP client does not send another message
    until it gets a response to the first message.
    """
    controlAction = QtCore.pyqtSignal(object)
    controlMessage = QtCore.pyqtSignal(object)
    gotConnection = QtCore.pyqtSignal(bool)
    
    def __init__(self, parallel_mode = None, server = None, verbose = True, **kwds):
        super().__init__(**kwds)
        self.parallel_mode = None
        self.server = server
        self.test_directory = None
        self.test_parameters = None
        self.verbose = verbose

        self.server.comGotConnection.connect(self.handleNewConnection)
        self.server.comLostConnection.connect(self.handleLostConnection)
        self.server.messageReceived.connect(self.handleMessageReceived)

    def actionDone(self, tcp_action):
        """
        This is called when an action completes.
        """
        data = tcp_action.getData()
        if "parameters" in data:
            self.test_parameters = data["parameters"]
        tcp_action.sendResponse(self.server)

    def cleanUp(self):
        self.server.close()
        
    def handleLostConnection(self):
        self.gotConnection.emit(False)

    def handleMessageReceived(self, tcp_message):
        """
        TCP message handling.
        """
        if self.verbose:
            print(">TCP message received:")
            print(tcp_message)
            print("")

        if tcp_message.isType('Check Focus Lock'):
            # This is supposed to ensure that everything else, like stage moves is complete.
            self.controlMessage.emit(halMessage.SyncMessage())
            
            action = TCPAction(tcp_message = tcp_message)
            self.controlAction.emit(action)

        elif tcp_message.isType('Find Sum'):
            # This is supposed to ensure that everything else, like stage moves is complete.
            self.controlMessage.emit(halMessage.SyncMessage())
            
            action = TCPAction(tcp_message = tcp_message)
            self.controlAction.emit(action)            
                
        elif tcp_message.isType("Set Directory"):
            print(">> Warning the 'Set Directory' message is deprecated.")
            directory = tcp_message.getData("directory")
            if not os.path.isdir(directory):
                tcp_message.setError(True, directory + " is an invalid directory")
            else:
                self.test_directory = directory
                if not tcp_message.isTest():
                    #
                    # We don't respond immediately to the client as we want to make sure
                    # that the HAL actually takes care of the directory change. Though
                    # this should happen really fast and it is not clear this step is
                    # necessary.
                    #
                    self.controlMessage.emit(halMessage.HalMessage(m_type = "change directory",
                                                                   data = {"directory" : directory},
                                                                   finalizer = lambda : self.server.sendMessage(tcp_message)))
                    return
            self.server.sendMessage(tcp_message)

        elif tcp_message.isType("Set Parameters"):
            if tcp_message.isTest():
                action = TCPActionGetParameters(tcp_message = tcp_message)
            else:
                action = TCPActionSetParameters(tcp_message = tcp_message)
            self.controlAction.emit(action)
                    
        elif tcp_message.isType("Take Movie"):

            # Check that movie length is valid.
            if (tcp_message.getData("length") is None) or (tcp_message.getData("length") < 1):
                tcp_message.setError(True, str(message.getData("length")) + " is an invalid movie length.")
                self.server.sendMessage(tcp_message)
                return

            # Some messy logic here to check if we will over-write a existing films? For now, just
            # verify that the movie.xml file does not exist.
            if not tcp_message.getData("overwrite"):
                directory = tcp_message.getData("directory")
                if directory is None:
                    directory = self.test_directory

                filename = os.path.join(directory, tcp_message.getData("name")) + ".xml"
                if os.path.exists(filename):
                    tcp_message.setError(True, "The movie file '" + filename + "' already exists.")
                    self.server.sendMessage(tcp_message)
                    return

            # More messy logic here to return film size, time, etc..
            if tcp_message.isTest():
                
                # If the movie has parameters specified, we'll request them specially.
                if tcp_message.getData("parameters") is not None:
                    action = TCPActionGetMovieStats(tcp_message = tcp_message)
                    self.controlAction.emit(action)

                # Otherwise calculate based on the current parameters.
                else:
                    calculateMovieStats(tcp_message, self.test_parameters)
                    self.server.sendMessage(tcp_message)                    
            else:
                action = TCPActionTakeMovie(tcp_message = tcp_message)
                self.controlAction.emit(action)

        else:
            if tcp_message.isTest() or (not self.parallel_mode):
                action = TCPAction(tcp_message = tcp_message)
                self.controlAction.emit(action)
            else:
                msg = halMessage.HalMessage(m_type = "tcp message",
                                            data = {"tcp message" : tcp_message})
                self.controlMessage.emit(msg)
                self.server.sendMessage(tcp_message)
                
    def handleNewConnection(self):
        self.gotConnection.emit(True)

    def setDirectory(self, directory):
        self.test_directory = directory

    def setParameters(self, parameters):
        self.test_parameters = parameters
        
        
class TCPControl(halModule.HalModule):
    """
    HAL TCP control module.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.control_action = None

        configuration = module_params.get("configuration")
        server = tcpServer.TCPServer(port = configuration.get("tcp_port"),
                                     server_name = "Hal",
                                     parent = self)
        self.control = Controller(parallel_mode = configuration.get("parallel_mode"),
                                  server = server,
                                  parent = self)
        self.control.controlAction.connect(self.handleControlAction)
        self.control.controlMessage.connect(self.handleControlMessage)

        # TCP messages are packaged into this HAL message.
        #
        # The module(s) that handle the message need to add a 'handled' response
        # so that we know that someone did something with the message.
        #
        halMessage.addMessage("tcp message",
                              validator = {"data" : {"tcp message" : [True, tcpMessage.TCPMessage]},
                                           "resp" : {"handled" : [True, bool]}})

    def cleanUp(self, qt_settings):
        self.control.cleanUp()

    def finalizeControlAction(self):
        self.control.actionDone(self.control_action)
        self.control_action.actionMessage.disconnect(self.sendMessage)
        self.control_action = None
        
    def handleControlAction(self, action):
        #
        # Actions will persist until some condition is met, at which point
        # a response is returned to the TCP client.
        #
        assert (self.control_action is None)
        
        self.control_action = action
        self.control_action.actionMessage.connect(self.sendMessage)
        self.sendMessage(self.control_action.getHalMessage())
        
    def handleControlMessage(self, message):
        #
        # For messages a response is immediately returned to the TCP client
        # even if the request is still being handled by HAL.
        #
        self.sendMessage(message)

    def handleGotConnection(self, connected):
        if connected:
            self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                                   data = {"properties" : {"connected" : True}}))
        else:
            #
            # If we are still processing a message just clean it up and
            # throw it away. Not sure if this is the right thing, but if
            # the Dave / Steve disconnects and reconnects then we are
            # going to have issues if we're still processing an action.
            #
            if self.control_action is not None:
                self.control_action.actionMessage.disconnect(self.sendMessage)
                self.control_action = None
                
            self.sendMessage(halMessage.HalMessage(m_type = "configuration",
                                                   data = {"properties" : {"connected" : False}}))

    def handleResponses(self, message):

        #
        # At 'configure2' we get the default parameters, we know this is
        # 'configure2' because this is the only time that self.control_action
        # is None.
        #
        if self.control_action is None:
            if message.isType("get parameters"):
                response = message.getResponses()[0]
                self.control.setParameters(response.getData()["parameters"])
        else:
            if self.control_action.handleResponses(message):
                self.finalizeControlAction()

    def processMessage(self, message):
        
        if self.control_action is not None:
            if self.control_action.processMessage(message):
                self.finalizeControlAction()

        if message.isType("change directory"):
            self.control.setDirectory(message.getData()["directory"])

        # At least for testing we'll need the default parameters.
        elif message.isType("configure2"):
            self.sendMessage(halMessage.HalMessage(m_type = "get parameters",
                                                   data = {"index or name" : 0}))

        elif message.isType("updated parameters"):
            self.control.setParameters(message.getData()["parameters"])



#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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

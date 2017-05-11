#!/usr/bin/env python
"""
Handles remote control (via TCP/IP of the data collection program)

Hazen 05/17
"""

import os
from PyQt5 import QtCore

import storm_control.sc_library.tcpMessage as tcpMessage
import storm_control.sc_library.tcpServer as tcpServer

import storm_control.hal4000.film.filmRequest as filmRequest
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


class Controller(QtCore.QObject):
    """
    ..
    """
    controlMessage = QtCore.pyqtSignal(object)
    
    def __init__(self, server = None, verbose = True, **kwds):
        super().__init__(**kwds)
        self.directory = None
        self.server = server
        self.tcp_message = None
        self.test_directory = None
        self.test_parameters = None
        self.verbose = verbose

        self.server.comGotConnection.connect(self.handleNewConnection)
        self.server.comLostConnection.connect(self.handleLostConnection)
        self.server.messageReceived.connect(self.handleMessageReceived)

    def cleanUp(self):
        self.server.close()

    def filmComplete(self):
        """
        This method will get called when film.film sends a 'film lockout' message with
        'locked out' False, which is the signal for the end of a film.

        Note: The 'None' check is because we could also end up here if the user 
              requested a film via the GUI (i.e. they clicked the record button).
        """
        if self.tcp_message is not None:
            self.server.sendMessage(self.tcp_message)
        self.tcp_message = None

    def getParametersComplete(self, parameters):
        """
        This method is called when settings.settings responds to a request for 
        parameters.
        """
        # FIXME: Need to check that the parameters are initialized.
        if parameters is None:
            self.tcp_message.setError(True, "Requested parameters not found")
        else:
            self.test_parameters = parameters
        self.server.sendMessage(self.tcp_message)
        self.tcp_message = None
        
    def handleLostConnection(self):
        self.test_directory = self.directory
        self.test_parameters = None
        self.controlMessage.emit(halMessage.HalMessage(m_type = "configuration",
                                                       data = {"properties" : {"connected" : False}}))

    def handleMessageReceived(self, tcp_message):
        """
        TCP message handling.
        """
        if self.verbose:
            print(">TCP message received:")
            print(tcp_message)
            print("")
        
        if tcp_message.isType("Set Directory"):
            print(">> Warning the 'Set Directory' message is deprecated.")
            directory = tcp_message.getData("directory")
            if not os.path.isdir(directory):
                tcp_message.setError(True, directory + " is an invalid directory")
            else:
                self.test_directory = directory
                if not tcp_message.isTest():
                    self.controlMessage.emit(halMessage.HalMessage(m_type = "change directory",
                                                                   data = {"directory" : directory},
                                                                   finalizer = lambda : self.server.sendMessage(tcp_message)))
                    return
            self.server.sendMessage(tcp_message)

        elif tcp_message.isType("Set Parameters"):

            # Fail if we are currently handling a different message.
            assert self.tcp_message is None
            
            if tcp_message.isTest():
                self.controlMessage.emit(halMessage.HalMessage(m_type = "get parameters",
                                                               data = {"index or name" : tcp_message.getData("parameters")}))
            else:
                self.controlMessage.emit(halMessage.HalMessage(m_type = "set parameters",
                                                               data = {"index or name" : tcp_message.getData("parameters")}))
                    
        elif tcp_message.isType("Take Movie"):

            # Check that movie length is valid.
            if (tcp_message.getData("length") is None) or (tcp_message.getData("length") < 1):
                tcp_message.setError(True, str(message.getData("length")) + " is an invalid movie length.")
                self.server.sendMessage(tcp_message)
                return

            # Some messy logic here to check if we will over-write a existing films? For now, just
            # verify that the movie.xml file does not exist.
            if not tcp_message.getData("overwrite"):
                directory = tcp_message.getData("directory"):
                if directory is None:
                    directory = self.test_directory

                filename = os.path.join(directory, tcp_message.getData("name")) + ".xml"
                if os.path.exists(filename):
                    tcp_message.setError(True, "The movie file '" + filename + "' already exists.")
                    self.server.sendMessage(tcp_message)
                    return

            # Fail if we are currently handling a different message.
            assert self.tcp_message is None

            if tcp_message.isTest():
                # More messy logic here to return film size, time, etc.. here.
                pass
            else:
                # Check if we need to change parameters first.
                if tcp_message.getData("parameters") is not None:
                    pass
                
                # Take movie.
                film_request = filmRequest.FilmRequest(basename = tcp_message.getData("name"),
                                                       directory = tcp_message.getData("directory"),
                                                       frames = tcp_message.getData("length"),
                                                       overwrite = tcp_message.getData("overwrite"),
                                                       tcp_request = True)
                self.controlMessage.emit(halMessage.HalMessage(m_type = "start film request",
                                                               data = {"request" : film_request}))
                self.tcp_message = tcp_message

        # Everything else is (in theory) handled by other modules.
        else:
            self.controlMessage.emit(halMessage.HalMessage(m_type = "tcp message",
                                                           data = {"tcp message" : tcp_message}))
    
    def handleNewConnection(self):
        self.controlMessage.emit(halMessage.HalMessage(m_type = "configuration",
                                                       data = {"properties" : {"connected" : True}}))

    def sendResponse(self, tcp_message, was_handled):
        if not was_handled:
            print(">> Warning no response to", tcp_message.getType())
            tcp_message.setError(True, "This message was not handled.")
        self.server.sendMessage(tcp_message)

    def setDirectory(self, directory):
        self.directory = directory
        
    def setParametersComplete(self, parameters):
        """
        This method will get called when settings.settings sends a 'updated parameters' which 
        is the signal that the parameters have been updated.

        Note: The 'None' check is because we could also end up here if the user 
              requested a film via the GUI (i.e. they clicked the record button).
        """
        if self.tcp_message is not None:
            self.server.sendMessage(self.tcp_message)
        self.tcp_message = None
        

class TCPControl(halModule.HalModule):
    """
    HAL TCP control module.
    """
    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)

        configuration = module_params.get("configuration")
        server = tcpServer.TCPServer(port = configuration.get("tcp_port"),
                                     server_name = "Hal",
                                     parent = self)
        self.control = Controller(server = server,
                                  parent = self)
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

    def handleControlMessage(self, message):
        self.sendMessage(message)

    def handleResponses(self, message):
        if message.isType("get parameters"):
            assert (len(message.getResponses()) == 1)
            self.control.getParametersComplete(message.getResponses()[0])

        elif message.isType("tcp message"):
            #
            # FIXME: We might want to check for 'True' responses? Not sure
            #        why we'd ever respond with 'False' however.
            #
            self.control.sendResponse(message.getData()["tcp message"],
                                      message.hasResponses())

    def processMessage(self, message):

        if message.isType("change directory"):
            self.control.setDirectory(message.getData()["directory"])
            
        elif message.isType("film lockout"):
            if not message.getData()["locked out"]:
                self.control.filmComplete()

        elif message.isType("updated parameters"):
            self.control.setParametersComplete(message.getData()["parameters"])

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

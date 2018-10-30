#!/usr/bin/env python
"""
Handles communication with HAL.

Hazen 10/18
"""
import warnings
from PyQt5 import QtCore

# Debugging
import storm_control.sc_library.hdebug as hdebug

# Communication with the acquisition software
import storm_control.sc_library.tcpClient as tcpClient
import storm_control.sc_library.tcpMessage as tcpMessage

import storm_control.steve.mosaicDialog as mosaicDialog


class Comm(QtCore.QObject):
    """
    Handles communication with HAL.

    The TCP/IP connection should be broken is Steve is idle so that
    user is not locked out of some of the features of HAL.
    """
    
    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        self.busy = False
        self.current_message = None

#        # Back stops breaking connections if a module fails
#        # to do this for some reason.
#        #
#        self.watch_dog_timer = QtCore.QTimer(self)
#        self.watch_dog_timer.setSingleShot(True)
#        self.watch_dog_timer.timeout.connect(self.handleWatchDogTimer)
#        self.watch_dog_timer_delay = 1000
        
        self.tcp_client = tcpClient.TCPClient(parent = self,
                                              port = 9000,
                                              server_name = "hal",
                                              verbose = True)
#        self.tcp_client.comLostConnection.connect(self.handleDisconnect)
        self.tcp_client.messageReceived.connect(self.handleMessageReceived)

    @hdebug.debug        
    def handleMessageReceived(self, message):
        self.busy = False

        # Save this property of the message as the message finalizer
        # could change self.current_message by creating a new message.
        disconnect = self.current_message.getDisconnect()

        # HAL only sends messages in response to requests, so we can
        # assume that the message we received is a response to the
        # last message that we sent.
        if not (message.getID() == self.current_message.getMessageID()):
            warnings.warn("Received a response to a different message.")
        elif message.hasError():
            err_msg = "tcp error: " + message.getErrorMessage()
            warnings.warn(err_msg)
            hdebug.logText(err_msg)
        else:
            # Warning! This can change self.current_message.
            self.current_message.finalizer(message)

        # Disconnect from HAL if requested. Note that if the message
        # finalizer created a new message this will be a NOP.
        if disconnect:
            self.stopCommunication()
            
    @hdebug.debug
    def isBusy(self):
        return self.busy
    
    @hdebug.debug
    def sendMessage(self, comm_message):

        # Ignore messages if we're already busy. Only one message at
        # a time..
        if self.isBusy():
            return
        
        self.busy = True
        self.current_message = comm_message

        # This method is a NOP if we're already connected.
        if self.tcp_client.startCommunication():
            self.tcp_client.sendMessage(self.current_message.getMessage())
        else:
            self.current_message = None
            warnings.warn("Cannot connect to HAL.")

    @hdebug.debug
    def stopCommunication(self):
        if not self.isBusy():
            self.tcp_client.stopCommunication()

            
class CommMessage(object):
    """
    Base message class.
    """
    @hdebug.debug
    def __init__(self, disconnect = True, finalizer_fn = None, **kwds):
        super().__init__(**kwds)

        # If this is True we'll disconnect from HAL when we receive the
        # message response.
        self.disconnect = disconnect
        
        # This function will be called when HALs response to a message
        # is received.
        self.finalizer_fn = finalizer_fn

        # This is the HAL message.
        self.tcp_message = None

    @hdebug.debug
    def getDisconnect(self):
        return self.disconnect

    @hdebug.debug
    def getMessage(self):
        return self.tcp_message

    @hdebug.debug
    def getMessageID(self):
        return self.tcp_message.getID()
    
    @hdebug.debug
    def finalizer(self, tcp_message_response):
        if self.finalizer_fn is not None:
            self.finalizer_fn(self.tcp_message, tcp_message_response)


class CommMessageMovie(CommMessage):
    """
    Take a movie.
    """
    @hdebug.debug
    def __init__(self, directory = "", filename = "", length = 1, **kwds):
        super().__init__(**kwds)
        
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Take Movie",
                                                 message_data = {"name" : filename,
                                                                 "directory" : directory,
                                                                 "length" : length})


class CommMessageMosaicSettings(CommMessage):
    """
    Query for mosaic settings.
    """
    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)
    
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Mosaic Settings")            


class CommMessageObjective(CommMessage):
    """
    Query for current objective.
    """
    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Objective")


class CommMessagePosition(CommMessage):
    """
    Query current stage position.
    """
    @hdebug.debug
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Stage Position")    


class CommMessageStage(CommMessage):
    """
    Move the stage to a position.
    """
    @hdebug.debug
    def __init__(self, stage_x = 0.0, stage_y = 0.0, **kwds):
        super().__init__(**kwds)

        self.tcp_message = tcpMessage.TCPMessage(message_type = "Move Stage",
                                                 message_data = {"stage_x":stage_x,
                                                                 "stage_y":stage_y})

    
#def objectiveMessage(is_other = False):
#    """
#    Creates a objective message for communication via TCPClient.
#    """
#    return tcpMessage.TCPMessage(message_type = "Get Objective",
#                                 message_data = {"is_other":is_other})
        

#def directoryMessage(directory):
#    """
#    Creates a change directory message.
#    
#    directory - The directory to change to.
#    """
#    return tcpMessage.TCPMessage(message_type = "Set Directory",
#                                 message_data = {"directory" : directory})

#def getPositionMessage():
#    """
#    Creates a get stage position message for communication via TCPClient.
#    """
#    return tcpMessage.TCPMessage(message_type = "Get Stage Position")



#
# The MIT License
#
# Copyright (c) 2018 Zhuang Lab, Harvard University
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

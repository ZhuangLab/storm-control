#!/usr/bin/env python
"""
Actions for TCP testing.

Hazen 04/17
"""

import storm_control.sc_library.tcpMessage as tcpMessage

import storm_control.hal4000.testing.testActions as testActions


class TestActionTCP(testActions.TestAction):
    """
    Base class for all TCP test actions.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = None

    def checkMessage(self, tcp_message):
        """
        Sub-class this to check that the TCP response 
        message is as expected.
        """
        pass
        
    def handleMessageReceived(self, tcp_message):
        """
        The default behavior as most actions are complete 
        when they get a response from HAL.
        """
        self.checkMessage(tcp_message)
        self.actionDone.emit()


class GetMosaicSettings(TestActionTCP):
    """
    Query HAL for the current mosaic settings.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Mosaic Settings")


class GetObjective(TestActionTCP):
    """
    Query HAL for the current objective.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Objective")

        
class GetStagePosition(TestActionTCP):
    """
    Query HAL for the current stage position.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Get Stage Position")


class MoveStage(TestActionTCP):
    """
    Tell HAL to move the XY stage.
    """
    def __init__(self, test_mode = False, x = None, y = None, **kwds):
        super().__init__(**kwds)
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Move Stage",
                                                 message_data = {"stage_x" : x,
                                                                 "stage_y" : y},
                                                 test_mode = test_mode)


class TakeMovie(TestActionTCP):
    """
    Tell HAL to take a movie.
    """
    def __init__(self,
                 directory = None,
                 length = None,
                 name = None,
                 overwrite = True,
                 test_mode = None,
                 **kwds):
        super().__init__(**kwds)
        self.directory = directory
        self.length = length
        self.name = name
        
        self.tcp_message = tcpMessage.TCPMessage(message_type = "Take Movie",
                                                 message_data = {"directory" : self.directory,
                                                                 "length" : self.length,
                                                                 "name": self.name,
                                                                 "overwrite" : overwrite},
                                                 test_mode = test_mode)

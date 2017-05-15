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


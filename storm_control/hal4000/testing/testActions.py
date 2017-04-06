#!/usr/bin/env python
"""
The basic test action as well as some sub-classes.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage


class TestAction(QtCore.QObject):
    """
    Base class for all test actions.
    """
    actionDone = QtCore.pyqtSignal()

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.m_type = "noop"
        
        self.action_timer = QtCore.QTimer(self)
        self.action_timer.timeout.connect(self.handleActionTimer)
        self.action_timer.setSingleShot(True)

    def getMessageData(self):
        return None

    def getMessageFilter(self):
        return "na"
    
    def getMessageType(self):
        return self.m_type

    def getResponseFilter(self):
        return self.m_type
        
    def getSourceName(self):
        return "testing"
    
    def finalizer(self):
        pass

    def handleActionTimer(self):
        self.actionDone.emit()

    def handleMessage(self, message):
        pass

    def handleResponses(self, message):
        pass

    def start(self):
        pass
    
    def startActionTimer(self, timeout):
        self.action_timer.setInterval(timeout)
        self.action_timer.start()
        

class Timer(TestAction):
    """
    Pause for the specified time in milliseconds.
    """
    def __init__(self, timeout = 0, **kwds):
        super().__init__(**kwds)
        self.timeout = timeout
    
    def start(self):
        self.startActionTimer(self.timeout)

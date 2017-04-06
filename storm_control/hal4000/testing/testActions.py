#!/usr/bin/env python
"""
The basic test action as well as some sub-classes.

Hazen 04/17
"""

from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halMessage as halMessage


class TestException(halExceptions.HalException):
    pass


class TestAction(QtCore.QObject):
    """
    Base class for all test actions.
    """
    actionDone = QtCore.pyqtSignal()

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.message = None
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

    def setMessage(self, message):
        self.message = message
        
    def start(self):
        pass
    
    def startActionTimer(self, timeout):
        self.action_timer.setInterval(timeout)
        self.action_timer.start()
        

class GetParameters(TestAction):
    """
    Get a parameters file from settings.settings
    """
    def __init__(self, p_name = "", **kwds):
        super().__init__(**kwds)

        self.m_type = "get parameters"
        self.p_name = p_name
        self.parameters = None

    def checkParameters(self):
        """
        Sub-classes should override this run tests on the 
        parameters that were returned.
        """
        pass
    
    def finalizer(self):
        if not self.message.hasResponses():
            raise TestException("No response to message '" + self.m_type + "'")            
        self.actionDone.emit()

    def getMessageData(self):
        return {"index or name" : self.p_name}
    
    def handleResponses(self, message):
        for response in message.getResponses():
            if self.parameters is None:
                self.parameters = response.getData()["parameters"]
            else:
                raise TestException("Multiple responses to '" + self.m_type + "'")
        self.checkParameters()


class LoadParameters(TestAction):
    """
    Load a parameters file.
    """
    def __init__(self, filename = "", is_default = False, **kwds):
        super().__init__(**kwds)

        self.filename = filename
        self.is_default = is_default
        self.m_type = "new parameters file"

    def finalizer(self):
        self.actionDone.emit()

    def getMessageData(self):
        return {"filename" : self.filename,
                "is_default" : self.is_default}


class SetParameters(TestAction):
    """
    Set current parameters.
    """
    def __init__(self, p_name = "", **kwds):
        super().__init__(**kwds)

        self.p_name = p_name
        self.m_type = "set parameters"

    def getMessageData(self):
        return {"index or name" : self.p_name}

    def getMessageFilter(self):
        return "updated parameters"

    def handleMessage(self, message):
        self.actionDone.emit()
        
    
class Timer(TestAction):
    """
    Pause for the specified time in milliseconds.
    """
    def __init__(self, timeout = 0, **kwds):
        super().__init__(**kwds)
        self.timeout = timeout
    
    def start(self):
        self.startActionTimer(self.timeout)

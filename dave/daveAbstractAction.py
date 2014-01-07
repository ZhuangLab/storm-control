#!/usr/bin/python
#
## @file
#
# An abstract class for a dave action
#
# Jeff 1/14
#

from PyQt4 import QtCore

## DaveAction
#
# The base class for a dave action.
#
class DaveAction(QtCore.QObject):

    # Define custom signal
    complete_signal = QtCore.pyqtSignal(str)
    error_signal = QtCore.pyqtSignal(str)
    
    ## __init__
    #
    # Default initialization.
    #
    def __init__(self, com_port, parent = None):

        # Initialize parent class
        QtCore.QObject.__init__(self, parent)

        # Connect com port
        self.com_port = com_port
        self.com_port.acknowledged.connect(self.handleAcknowledge)
        self.com_port.complete.connect(self.handleComplete)

        # Initialize error message
        self.error_message = ""

        # Initialize internal timer
        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.handleTimerDone)
        self.delay = 0

        # Define complete requirements
        self.complete_on_acknowledge = False
        self.complete_on_timer = False
        
    ## abort
    #
    # Handle an external abort call
    #
    def abort(self):
        self.sendComplete()

    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        self.com_port.acknowledged.disconnect()
        self.com_port.complete.disconnect()

    ## completeAction
    #
    # Handle the completion of an action
    #
    def completeAction(self):
        self.com_port.stopCommunication()
        self.complete_signal.emit(self.error_message)

    ## getError
    #
    # @return The error message if there a problem occured during this action.
    #
    def getError(self):
        return self.error_message

    ## handleAcknowledged
    #
    # handle the com port acknowledge signal
    #
    def handleAcknowledged(self):
        if self.complete_on_acknowledge:
            self.completeAction()
        elif self.delay > 0:
            self.delay_timer.start(self.delay)

    ## handleComplete
    #
    # handle the com port complete signal
    #
    # @param a_string The complete message from the comp port (as a string).
    #
    def handleComplete(self, a_string):
        self.error_message = ""
        self.completeAction()

    ## handleTimerDone
    #
    # Handle a timer done signal
    #
    def handleTimerDone(self):
        if self.complete_on_timer:
            self.completeAction()

    ## start
    #
    # Start the desired action. Must be overloaded. 
    #
    def start(self):
        self.com_port.startCommunication()


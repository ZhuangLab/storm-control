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
    complete_signal = QtCore.pyqtSignal()
    error_signal = QtCore.pyqtSignal(str)
    
    ## __init__
    #
    # Default initialization.
    #
    def __init__(self, tcp_client, parent = None):

        # Initialize parent class
        QtCore.QObject.__init__(self, parent)

        # Connect com port
        self.tcp_client = tcp_client
        self.tcp_client.acknowledged.connect(self.handleAcknowledged)
        self.tcp_client.complete.connect(self.handleComplete)

        # Initialize error message
        self.error_message = ""
        self.should_pause_after_error = True

        # Initialize internal timer
        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.handleTimerDone)
        self.delay = 0

        # Define complete requirements
        self.complete_on_acknowledge = False
        self.complete_on_timer = False

        # Define pause after completion state
        self.should_pause = False

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
        self.tcp_client.acknowledged.disconnect()
        self.tcp_client.complete.disconnect()

    ## completeAction
    #
    # Handle the completion of an action
    #
    def completeAction(self):
        self.tcp_client.stopCommunication()
        self.complete_signal.emit()

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
    def handleComplete(self):
        self.completeAction()

    ## completeActionWithError
    #
    # Send an error message if needed
    #
    def completeActionWithError(self):
        if self.should_pause_after_error == True:
            self.should_pause = True
        self.tcp_client.stopCommunication()
        self.error_signal.emit(self.error_message)

    ## handleTimerDone
    #
    # Handle a timer done signal
    #
    def handleTimerDone(self):
        if self.complete_on_timer:
            self.completeAction()

    ## shouldPause
    #
    # Determine if the command engine should pause after this action
    #
    def shouldPause(self):
        return self.should_pause

    ## start
    #
    # Start the desired action. Must be overloaded. 
    #
    def start(self):
        self.tcp_client.startCommunication()


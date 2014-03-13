#!/usr/bin/python
#
## @file
#
# An abstract class for a dave action
#
# Jeff 1/14 
#

from PyQt4 import QtCore
from sc_library.tcpMessage import TCPMessage

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
        self.message = TCPMessage()

        # Initialize error message
        self.error_message = ""
        self.should_pause_after_error = True

        # Initialize internal timer
        self.delay_timer = QtCore.QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.handleTimerDone)
        self.delay = 100 # Default delay

        # Define complete requirements
        self.complete_on_timer = False # Complete self.delay ms after acknowledgement of command received
                                       # Otherwise complete upon receipt of response message
            
        # Define pause after completion state
        self.should_pause = False

    ## abort
    #
    # Handle an external abort call
    #
    def abort(self):
        self.completeAction()

    ## cleanUp
    #
    # Handle clean up of the action
    #
    def cleanUp(self):
        self.tcp_client.message_ready.disconnect()

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

    ## handleReply
    #
    # handle the return of a message
    #
    def handleReply(self, message):
        # Check to see if the same message got returned
        if not (message.getID() == self.message.getID()):
            self.error_message = "Communication Error: Incorrect Message Returned"
            self.completeActionWithError()
        elif message.hasError():
            self.error_message = message.getErrorMessage()
            self.completeActionWithError()
        else: # Correct message and no error
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

    ## setTest
    #
    # Converts the Dave Action to a test request
    #
    def setTest(self, boolean):
        self.message.test = boolean

    ## shouldPause
    #
    # Determine if the command engine should pause after this action
    #
    def shouldPause(self):
        return self.should_pause

    ## start
    #
    # Start the action.
    #
    def start(self):
        self.tcp_client.message_ready.connect(self.handleReply)
        self.tcp_client.startCommunication()
        self.tcp_client.sendMessage(self.message)

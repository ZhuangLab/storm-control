#!/usr/bin/python
#
## @file
#
# Collection of classes that control the establish the basic operation of dave
# as it issues various types of commands to HAL and Kilroy
#
# Hazen 06/13; Jeff 1/14 
#

from sc_library.tcpMessage import TCPMessage

## DaveAction
#
# The base class for a dave action.
#
class DaveAction(QtCore.QObject):

    # Define custom signal
    complete_signal = QtCore.pyqtSignal(object)
    error_signal = QtCore.pyqtSignal(object)
    
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
        self.message.markAsComplete()
        self.completeAction(self.message)

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
    def completeAction(self, message):
        self.tcp_client.stopCommunication()
        self.complete_signal.emit(message)

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
            message.setError(True,"Communication Error: Incorrect Message Returned")
            self.completeActionWithError(message)
        elif message.hasError():
            self.completeActionWithError(message)
        else: # Correct message and no error
            self.completeAction(message)

    ## completeActionWithError
    #
    # Send an error message if needed
    #
    def completeActionWithError(self, message):
        if self.should_pause_after_error == True:
            self.should_pause = True
        self.tcp_client.stopCommunication()
        self.error_signal.emit(message)

    ## handleTimerDone
    #
    # Handle a timer done signal
    #
    def handleTimerDone(self):
        if self.complete_on_timer:
            self.message.markAsComplete()
            self.completeAction(self.message)

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


# ----------------------------------------------------------------------------------------
# Specific Actions
# ----------------------------------------------------------------------------------------

## FindSum
#
# The find sum action.
#
class FindSum(DaveAction):

    ## __init__
    #
    # @param min_sum The minimum sum that we should get from HAL upon completion of this action.
    #
    def __init__(self, tcp_client, min_sum):
        DaveAction.__init__(self, tcp_client)
        self.message = TCPMessage(message_type = "Focus Lock",
                                  message_data = {"command":"find_sum",
                                                  "min_sum": min_sum})

## MoveStage
#
# The movie parameters action.
#
class MoveStage(DaveAction):

    ## __init__
    #
    # @param command A XML command object.
    #
    def __init__(self, tcp_client, command):
        DaveAction.__init__(self, tcp_client)
        self.message = TCPMessage(message_type = "Move Stage",
                                  message_data = {"stage_x":command.stage_x,
                                                  "stage_y":command.stage_y})
            
## DaveActionMovie
#
# The movie acquisition action.
#
class DaveActionMovie(DaveAction):

    ## __init__
    #
    # @param movie A movie XML object.
    #
    def __init__(self, tcp_client, movie):
        DaveAction.__init__(self, tcp_client)
        self.movie = movie
        movie_data = movie.__dict__

        print movie
        print "Movie Data", movie_data
        if "progression" in movie_data:
            del movie_data["progression"]
            print movie_data
##            if hasattr(movie.progression, "type"):
##                movie_data["progression_type"] = movie.progression.type
##            if hasattr(movie.progression, "channels"):
##                movie_data["progression_channels"] = movie.progression.channels
##            if hasattr(movie.progressions, "filename"):
##                movie_data["progression_filename"] = movie.progression.filename
    
        # Create TCP Message Dictionary
        self.message = TCPMessage(message_type = "Movie",
                                  data = movie_data)

        print self.message

    ## abort
    #
    # Aborts the movie 
    #
    def abort(self):
        stop_message = TCPMessage(message_type = "abortMovie")
        self.message = stop_message
        self.tcp_client.sendMessage(self.message)


## DaveActionMovieParameters
#
# The movie parameters action.
#
class DaveActionMovieParameters(DaveAction):

    ## __init__
    #
    # @param movie A XML movie object.
    #
    def __init__(self, tcp_client, movie):
        DaveAction.__init__(self, tcp_client)
        self.delay = movie.delay
        self.movie = movie
        self.should_pause = self.movie.pause
        self.complete_on_timer = True

        movie_data = {}
        if hasattr(movie, "parameters"): movie_data["parameters"] = movie.parameters
        if hasattr(movie, "stage_x"): movie_data["stage_x"] = movie.stage_x
        if hasattr(movie, "stage_y"): movie_data["stage_y"] = movie.stage_y
        if hasattr(movie, "lock_target"): movie_data["lock_target"] = movie.lock_target

        self.message = TCPMessage(message_type = "Movie Parameters", message_data = movie_data)

## DaveActionRecenter
#
# The piezo recentering action. Note that this is only useful if the microscope
# has a motorized Z.
#
class DaveActionRecenter(DaveAction):
    ## __init__
    #
    # Create the object, set the delay time to 200 milliseconds.
    #
    def __init__(self, tcp_client):
        DaveAction.__init__(self, tcp_client)
        self.delay = 200
        self.message = TCPMessage(message_type = "Recenter")

## DaveActionValveProtocol
#
# The fluidics protocol action. Send commands to Kilroy.
#
class DaveActionValveProtocol(DaveAction):
    ## __init__
    #
    # Initialize the valve protocol action
    #
    # @param protocols A valve protocols xml object
    #
    def __init__(self, tcp_client, protocol_xml):
        DaveAction.__init__(self, tcp_client)
        self.protocol_name = protocol_xml.protocol_name
        self.protocol_is_running = False

        self.message = TCPMessage(message_type = "Kilroy Protocol",
                                  message_data = {"name": self.protocol_name})

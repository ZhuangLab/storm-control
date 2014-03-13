#!/usr/bin/python
#
## @file
#
# Collection of classes that control the establish the basic operation of dave
# as it issues various types of commands to HAL and Kilroy
#
# Hazen 06/13; Jeff 1/14 
#

from daveAbstractAction import DaveAction

## DaveActionFindSum
#
# The find sum action.
#
class DaveActionFindSum(DaveAction):

    ## __init__
    #
    # @param min_sum The minimum sum that we should get from HAL upon completion of this action.
    #
    def __init__(self, tcp_client, min_sum):
        DaveAction.__init__(self, tcp_client)
        self.min_sum = min_sum
        self.message = TCPMessage(message_type = "Find Sum",
                                  data = {"min_sum": min_sum})

    ## handleReply
    #
    # @param message. The response from Hal.
    #
    def handleReply(self, message):
        if message.getType() == "Find Sum" and message.isComplete():
            if message.getData("sum") > self.min_sum:
                self.completeAction()
            else:
                self.error_message = "Sum signal " + str(message.getData("Sum")) + " is below threshold value of " + str(self.min_sum)
                self.completeActionWithError()
        else:
            self.error_message = "Communication Error"
            self.completeActionWithError()
            
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

        # Create TCP Message Dictionary
        movie_data = movie.__dict__()                
        self.message = TCPMessage(message_type = "Movie",
                                  data = movie_data)

    ## abort
    #
    # Aborts the movie 
    #
    def abort(self):
        stop_message = TCPMessage(message_type = "Abort")
        self.message = stop_message
        self.tcp_client.sendMessage(self.message)

    ## handleReply
    #
    # Returns no error if a_string is "NA" or int(a_string) is greater than the
    # minimum number of spots that the movie should have (as specified by
    # the movie XML object).
    #
    # @param a_string The response from HAL.
    #
    def handleReply(self, message):
        if message.getType() == "Movie" and message.isComplete():
            if message.getData("num_spots") > self.movie.min_spots:
                self.completeAction()
            else:
                self.error_message = "Sum signal " + str(message.getData("Sum")) + " is below threshold value of " + str(self.min_sum)
                self.completeActionWithError()
        elif message.getType() == "Abort" and message.isComplete():
            self.completeAction()
        else:
            self.error_message = "Communication Error"
            self.completeActionWithError()

    ## start
    #
    # Send the startMovie command to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self):
        DaveAction.start(self)

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
        
    ## start
    #
    # Send  the movie parameters command to HAL.
    #
    def start(self):
        DaveAction.start(self)
        self.tcp_client.sendMovieParameters(self.movie)

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

    ## start
    #
    # Send the recenter piezo command to HAL.
    #
    def start(self):
        DaveAction.start(self)
        self.tcp_client.startRecenterPiezo()

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

    ## handleComplete
    #
    # Handle a complete message from the kilroyClient.
    #
    # @param a_string The complete message from kilroy
    #
    def handleComplete(self, a_string):
        print "Received Complete from Kilroy " + a_string
        self.protocol_is_running = False
        self.completeAction()

    ## start
    #
    # Start sending protocols to kilroy
    #
    # @param comm A kilroy client object.
    #
    def start(self):
        DaveAction.start(self)
        self.protocol_is_running = True
        self.tcp_client.sendProtocol(self.protocol_name)

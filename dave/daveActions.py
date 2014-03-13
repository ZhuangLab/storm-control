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
from sc_library.tcpMessage import TCPMessage

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
        if hasattr(movie, "parameters"): movie_data["parameters"] = movie.paraeters
        if hasattr(movie, "stage_x"): movie_data["stage_x"] = movie.stage_x
        if hasattr(movie, "stage_y"): movie_data["stage_y"] = movie.stage_y
        if hasattr(movie, "lock_target"): movie_data["lock_target"] = movie.lock_target

        self.message = TCPMessage(message_type = "Movie Parameters", data = movie_data)

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
                                  data = {"name": self.protocol_name})

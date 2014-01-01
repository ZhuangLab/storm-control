#!/usr/bin/python
#
## @file
#
# Collection of classes that control the establish the basic operation of dave
# as it issues various types of commands to HAL and Kilroy
#
# Hazen 06/13; Jeff 12/13
#

## DaveAction
#
# The base class for actions that can be performed as part of taking a movie.
#
class DaveAction():

    ## __init__
    #
    # Default initialization.
    #
    def __init__(self):
        self.delay = 0
        self.message = ""
        self.comm_type = "HAL" # The default TCP Client to use
        
    ## abort
    #
    # The default behaviour is not to do anything.
    #
    # @param comm A tcpClient object.
    #
    def abort(self, comm):
        pass

    ## getCommType
    #
    # @return The client to use for TCP/IP communication with this action.
    #
    def getCommType(self):
        return self.comm_type

    ## getMessage
    #
    # @return The error message if there a problem occured during this action.
    #
    def getMessage(self):
        return self.message

    ## handleAcknowledged
    #
    # This is called when we get command acknowledgement from HAL. If this
    # returns true and the delay time is greater than zero then the delay
    # timer is started.
    #
    # @return True.
    #
    def handleAcknowledged(self):
        return True

    ## handleComplete
    #
    # This is called when we get a complete message from HAL with a_string
    # containing the contents of the complete message. If it returns true
    # then we continue to the next action, otherwise we stop taking movies.
    #
    # @param a_string The complete message from HAL (as a string).
    #
    # @return True
    #
    def handleComplete(self, a_string):
        return True

    ## shouldPause
    #
    # @return True/False if movie acquisition should pause after taking this movie, the default is False.
    #
    def shouldPause(self):
        return False

    ## start
    #
    # The default behaviour is not do anything.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        pass

    ## startTimer
    #
    # If there is a delay time for this action then set the interval of the provided timer, start it
    # and return True, otherwise return False.
    #
    # @param timer A PyQt timer.
    #
    # @return True/False if we started timer.
    #
    def startTimer(self, timer):
        if (self.delay > 0):
            timer.setInterval(self.delay)
            timer.start()
            return True
        else:
            return False


## DaveActionFindSum
#
# The find sum action.
#
class DaveActionFindSum(DaveAction):

    ## __init__
    #
    # @param min_sum The minimum sum that we should get from HAL upon completion of this action.
    #
    def __init__(self, min_sum):
        DaveAction.__init__(self)
        self.min_sum = min_sum

    ## handleAcknowledged
    #
    # @return False.
    #
    def handleAcknowledged(self):
        return False

    ## handleComplete
    #
    # @param a_string The sum signal message from HAL.
    #
    # @return True/False if float(a_string) is greater than min_sum.
    #
    def handleComplete(self, a_string):
        if (a_string == "NA") or (float(a_string) > self.min_sum):
            return True
        else:
            self.message = "Sum signal " + a_string + " is below threshold value of " + str(self.min_sum)
            return False

    ## start
    #
    # Send the startFindSum message to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        comm.startFindSum()


## DaveActionMovie
#
# The movie acquisition action.
#
class DaveActionMovie(DaveAction):

    ## __init__
    #
    # @param movie A movie XML object.
    #
    def __init__(self, movie):
        DaveAction.__init__(self)
        self.acquiring = False
        self.movie = movie

    ## abort
    #
    # Aborts the movie (if we are current acquiring).
    #
    # @param comm A tcpClient object.
    #
    def abort(self, comm):
        if self.acquiring:
            comm.stopMovie()

    ## handleAcknowledged
    #
    # @return True.
    #
    def handleAcknowledged(self):
        return False

    ## handleComplete
    #
    # Returns false if a_string is "NA" or int(a_string) is greater than the
    # minimum number of spots that the movie should have (as specified by
    # the movie XML object).
    #
    # @param a_string The response from HAL.
    #
    # @return True/False if the movie was good.
    #
    def handleComplete(self, a_string):
        self.acquiring = False
        if (a_string == "NA") or (int(a_string) >= self.movie.min_spots):
            return True
        else:
            self.message = "Spot finder counts " + a_string + " is below threshold value of " + str(self.movie.min_spots)
            return False

    ## start
    #
    # Send the startMovie command to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        self.acquiring = True
        comm.startMovie(self.movie)


## DaveActionMovieParameters
#
# The movie parameters action.
#
class DaveActionMovieParameters(DaveAction):

    ## __init__
    #
    # @param movie A XML movie object.
    #
    def __init__(self, movie):
        DaveAction.__init__(self)
        self.delay = movie.delay
        self.movie = movie

    ## shouldPause
    #
    # @return The pause time specified by the movie object.
    #
    def shouldPause(self):
        return self.movie.pause

    ## start
    #
    # Send  the movie parameters command to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        comm.sendMovieParameters(self.movie)


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
    def __init__(self):
        DaveAction.__init__(self)
        self.delay = 200

    ## handleAcknowledged
    #
    # @return False
    #
    def handleAcknowledged(self):
        return False

    ## start
    #
    # Send the recenter piezo command to HAL.
    #
    # @param comm A tcpClient object.
    #
    def start(self, comm):
        comm.startRecenterPiezo()

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
    def __init__(self, protocol_xml):
        DaveAction.__init__(self)
        self.comm_type = "Kilroy"
        self.protocol_name = protocol_xml.protocol_name
        self.protocol_is_running = False
        
    ## abort
    #
    # Does nothing for now
    #
    # @param comm A kilroy client object.
    #
    def abort(self, comm):
        pass

    ## handleAcknowledged
    #
    # Proceed to the next action when command is acknowledged?
    #
    def handleAcknowledged(self):
        return False

    ## handleComplete
    #
    # Handle a complete message from the kilroyClient. Does nothing for now.
    #
    # @param a_string The complete message from kilroy
    #
    # @return True
    #
    def handleComplete(self, a_string):
        print "Received Complete from Kilroy " + a_string
        self.protocol_is_running = True
        return True

    ## shouldPause
    #
    # @return True/False if movie acquisition should pause after taking this movie, the default is False.
    #
    def shouldPause(self):
        return False
        
    ## start
    #
    # Start sending protocols to kilroy
    #
    # @param comm A kilroy client object.
    #
    def start(self, comm):
        self.protocol_is_running = True
        comm.sendProtocol(self.protocol_name)

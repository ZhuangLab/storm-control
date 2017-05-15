#!/usr/bin/env python
import os

import storm_analysis.sa_library.datareader as datareader

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testActionsTCP as testActionsTCP
import storm_control.hal4000.testing.testing as testing

import storm_control.test as test


#
# Test "Get Mosaic Settings" message.
#
class GetMosaicSettingsAction1(testActionsTCP.GetMosaicSettings):

    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("obj1") == "100x,0.160,0.0,0.0")

class GetMosaicSettings1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetMosaicSettingsAction1()]

#
# Test "Get Objective" message.
#
class GetObjectiveAction1(testActionsTCP.GetObjective):

    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("objective") == "100x")

class GetObjective1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetObjectiveAction1()]

#
# Test "Get Stage Position" message.
#
class GetStagePositionAction1(testActionsTCP.GetStagePosition):

    def __init__(self, x = 0.0, y = 0.0, **kwds):
        super().__init__(**kwds)
        self.x = x
        self.y = y
        
    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("stage_x") == self.x)
        assert(tcp_message.getResponse("stage_y") == self.y)

class GetStagePosition1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetStagePositionAction1()]

#
# Test "Move Stage" message.
#
class MoveStageAction1(testActionsTCP.MoveStage):
        
    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("duration") == 1)

class MoveStage1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        #
        # We have to pause for 200ms so that the stage
        # a chance to update it's position.
        #
        x = 10.0
        y = 10.0
        self.test_actions = [testActionsTCP.MoveStage(x = x, y = y),
                             testActions.Timer(200),
                             GetStagePositionAction1(x = x, y = y),
                             MoveStageAction1(test_mode = True, x = 0.0, y = 0.0)]

#
# Test "Take Movie" message.
#
class TakeMovieAction1(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        movie = datareader.inferReader(os.path.join(self.directory, self.name + ".dax"))
        assert(movie.filmSize() == [512, 512, self.length])
        
class TakeMovie1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)
            
        self.test_actions = [TakeMovieAction1(directory = directory,
                                              length = 5,
                                              name = filename)]

class TakeMovieAction2(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        assert tcp_message.hasError()

class TakeMovie2(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)
            
        self.test_actions = [TakeMovieAction1(directory = directory,
                                              length = 5,
                                              name = filename),
                             TakeMovieAction2(directory = directory,
                                              length = 2,
                                              name = filename,
                                              overwrite = False),
                             TakeMovieAction2(directory = directory,
                                              length = 2,
                                              name = filename,
                                              overwrite = False,
                                              test_mode = True),
                             TakeMovieAction1(directory = directory,
                                              length = 5,
                                              name = filename)]

class TakeMovieAction3(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("disk_usage") == 25.0)
        assert(tcp_message.getResponse("duration") == 1.0)

class TakeMovie3(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"
            
        self.test_actions = [TakeMovieAction3(directory = directory,
                                              length = 50,
                                              name = filename,
                                              test_mode = True)]


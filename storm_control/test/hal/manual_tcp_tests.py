#!/usr/bin/env python
"""
Long runnings tests that are run manually, not designed for CI
"""
import os

import storm_analysis.sa_library.datareader as datareader

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testActionsTCP as testActionsTCP
import storm_control.hal4000.testing.testing as testing

import storm_control.test as test
import storm_control.test.hal.tcp_tests as tcpTests


class MoveStage1(testing.TestingTCP):
    """
    This tests repeated motion.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.reps = 10
        self.test_actions = [testActionsTCP.MoveStage(x = 10.0, y = 10.0),
                             tcpTests.GetStagePositionAction1(x = 10.0, y = 10.0),
                             testActionsTCP.MoveStage(x = 0.0, y = 0.0),
                             tcpTests.GetStagePositionAction1(x = 0.0, y = 0.0)]


class StandardDaveSequenceTakeMovieAction1(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        movie = datareader.inferReader(os.path.join(self.directory, self.name + ".dax"))
        assert(movie.filmSize() == [256, 256, self.length])

        
class StandardDaveSequenceTakeMovieAction2(testActionsTCP.TakeMovie):
        
    def checkMessage(self, tcp_message):
        movie = datareader.inferReader(os.path.join(self.directory, self.name + ".dax"))
        assert(movie.filmSize() == [256, 512, self.length])
        
        
class StandardDaveSequence1(testing.TestingTCP):
    """
    Multiple movie acquisition sequence that is normally used in Dave.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()

        self.reps = 1

        # Initial setup.
        #
        
        # Lock focus.
        self.test_actions.append(tcpTests.SetFocusLockModeAction1(mode_name = "Always On", locked = True))

        # Load parameters.
        self.test_actions.append(testActions.LoadParameters(filename = test.halXmlFilePathAndName("256x256.xml")))
        self.test_actions.append(testActions.LoadParameters(filename = test.halXmlFilePathAndName("256x512.xml")))

        # Turn off live mode.
        self.test_actions.append(testActions.SetLiveMode(live_mode = False))

        # Pause a second so that setup completes.
        self.test_actions.append(testActions.Timer(1000))
                             
        # Add loop parameters.
        for i in range(1):

            ## Position 0
            
            # Move stage.
            self.test_actions.append(testActionsTCP.MoveStage(x = 0.0, y = 0.0))

            # Check focus.
            self.test_actions.append(testActionsTCP.CheckFocusLock(focus_scan = False, num_focus_checks = 30))

            # Set parameters.
            self.test_actions.append(tcpTests.SetParametersAction1(name_or_index = "256x256"))

            # Take Movie.
            self.test_actions.append(StandardDaveSequenceTakeMovieAction1(directory = directory,
                                                                          length = 5,
                                                                          name = "movie_01"))

            # Remove movie.
            self.test_actions.append(testActions.RemoveFile(directory = directory,
                                                            name = "movie_01"))
            
            ## Position 1
            
            # Move stage.
            self.test_actions.append(testActionsTCP.MoveStage(x = 10.0, y = 0.0))

            # Check focus.
            self.test_actions.append(testActionsTCP.CheckFocusLock(focus_scan = False, num_focus_checks = 30))

            # Set parameters.
            self.test_actions.append(tcpTests.SetParametersAction1(name_or_index = "256x512"))

            # Take Movie.
            self.test_actions.append(StandardDaveSequenceTakeMovieAction2(directory = directory,
                                                                          length = 5,
                                                                          name = "movie_02"))

            # Remove movie.
            self.test_actions.append(testActions.RemoveFile(directory = directory,
                                                            name = "movie_02"))
            

class TakeMovie1(testing.TestingTCP):
    """
    Repeatedly request a movie by TCP and verify that it is taken & the correct size.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_01"

        self.reps = 10
        self.test_actions = [testActions.RemoveFile(directory = directory,
                                                    name = filename),
                             tcpTests.TakeMovieAction1(directory = directory,
                                                       length = 5,
                                                       name = filename)]

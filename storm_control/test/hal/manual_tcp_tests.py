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

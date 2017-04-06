#!/usr/bin/env python

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testing as testing

import storm_control.test as test


#
# Test taking a 10 frame movie, 512 x 512.
#
class FilmTest1(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.SetDirectory(directory = test.dataDirectory()),
                             testActions.Record(filename = "movie_01")]

#
# Test taking movies with feeds.
#
class FilmTest2(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.SetDirectory(directory = test.dataDirectory()),
                             testActions.LoadParameters(filename = test.halXmlFilePathAndName("feed_examples.xml")),
                             testActions.SetParameters(p_name = 0),
                             testActions.Record(filename = "movie_02")]



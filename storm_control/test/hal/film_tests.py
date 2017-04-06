#!/usr/bin/env python
import os

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

#
# Test that we can load the parameters files from a movie.
#
class FilmTest3(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        self.test_actions = [testActions.SetDirectory(directory = directory),
                             testActions.Record(filename = "movie_03"),
                             testActions.LoadParameters(os.path.join(directory, "movie_03.xml")),
                             testActions.SetParameters(p_name = 0),
                             testActions.Timer(timeout = 500)]

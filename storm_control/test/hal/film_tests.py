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

        directory = test.dataDirectory()
        filename = "movie_01"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)

        self.test_actions = [testActions.SetDirectory(directory = directory),
                             testActions.Record(filename = filename)]

#
# Test taking movies with feeds.
#
class FilmTest2(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_02"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)
            
        self.test_actions = [testActions.SetDirectory(directory = directory),
                             testActions.LoadParameters(filename = test.halXmlFilePathAndName("feed_examples.xml")),
                             testActions.SetParameters(p_name = 0),
                             testActions.Timer(timeout = 1000),
                             testActions.Record(filename = filename),
                             testActions.Timer(timeout = 2000)]

#
# Test that we can load the parameters files from a movie.
#
class FilmTest3(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        directory = test.dataDirectory()
        filename = "movie_03"

        # Remove old movie (if any).
        fullname = os.path.join(directory, filename + ".dax")
        if os.path.exists(fullname):
            os.remove(fullname)
            os.remove(os.path.join(directory, filename + ".xml"))
            
        self.test_actions = [testActions.SetDirectory(directory = directory),
                             testActions.Record(filename = filename),
                             testActions.LoadParameters(os.path.join(directory, "movie_03.xml")),
                             testActions.SetParameters(p_name = 0),
                             testActions.Timer(timeout = 500)]

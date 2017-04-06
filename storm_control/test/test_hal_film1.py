#!/usr/bin/env python
import os

import storm_analysis.sa_library.datareader as datareader

from storm_control.test.hal.standardHalTest import halTest
import storm_control.test as test

def test_hal_film():

    # This is expected to record a movie called 'movie_01.dax'
    halTest(config_xml = "none_classic_config.xml",
            class_name = "FilmTest1",
            test_module = "storm_control.test.hal.film_tests")

    # Check that the movie is the right length.
    movie = datareader.inferReader(os.path.join(test.dataDirectory(), "movie_01.dax"))
    assert(movie.filmSize() == [512, 512, 10])

    
if (__name__ == "__main__"):
    test_hal_film()

#!/usr/bin/env python
import os

import storm_analysis.sa_library.datareader as datareader

from storm_control.test.hal.standardHalTest import halTest
import storm_control.test as test

def test_hal_film():

    # This is expected to record several movies with names starting with 'movie_02'
    halTest(config_xml = "none_classic_config.xml",
            class_name = "FilmTest2",
            test_module = "storm_control.test.hal.film_tests")

    # Check that the movies are the right length.
    for name, size in [["movie_02.dax", [512, 512, 10]],
                       ["movie_02_average.dax", [512, 512, 1]],
                       ["movie_02_interval.dax", [256, 508, 2]],
                       ["movie_02_slice1.dax", [65, 64, 10]]]:
        movie = datareader.inferReader(os.path.join(test.dataDirectory(), name))
        assert(movie.filmSize() == size)

    
if (__name__ == "__main__"):
    test_hal_film()

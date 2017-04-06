#!/usr/bin/env python

from storm_control.test.hal.standardHalTest import halTest
import storm_control.test as test

def test_hal_film():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "FilmTest3",
            test_module = "storm_control.test.hal.film_tests")
    
if (__name__ == "__main__"):
    test_hal_film()

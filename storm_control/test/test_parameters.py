#!/usr/bin/env python
"""
Tests of the parameters object functionality.
"""

import storm_control.test as test

import storm_control.sc_library.parameters as params


def test_parameters_1():

    # Load parameters.
    p1 = params.parameters(test.xmlFilePathAndName("test_parameters.xml"), recurse = True)
    
    # Check a parameter.
    assert (p1.get("camera1.flip_horizontal") == False)

    # Change it's value.
    p1.set("camera1.flip_horizontal", True)

    # Check again.
    assert (p1.get("camera1.flip_horizontal") == True)


def test_parameters_2():

    # Load parameters.
    p1 = params.parameters(test.xmlFilePathAndName("test_parameters.xml"), recurse = True)

    # Copy.
    p2 = p1.copy()

    # Check that p1 and p2 store the same values and have
    # the same structure.

    # Change a value in p2.
    p2.set("camera1.flip_horizontal", True)

    # Check that p1 is still the same.
    assert (p1.get("camera1.flip_horizontal") == False)

    # Get the difference between p1 and p2.
    

if (__name__ == "__main__"):
    test_parameters_1()
    test_parameters_2()
    

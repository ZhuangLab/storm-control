#!/usr/bin/env python
"""
Tests of the parameters object functionality.
"""

import storm_control.sc_library.parameters as params

def test_parameters():
    
    # Load parameters.
    p1 = params.parameters("./data/test_parameters.xml", recurse = True)
    
    # Check a parameter.
    assert (p1.get("camera1.flip_horizontal") == False)

    # Change it's value.
    p1.set("camera1.flip_horizontal", True)

    # Check again.
    assert (p1.get("camera1.flip_horizontal") == True)

    # Copy.
    p2 = p1.copy()

    # Check that p1 and p2 store the same values.

    # Change a value in p2.
    p2.set("camera1.flip_horizontal", False)

    # Check that p1 is still the same.
    assert (p1.get("camera1.flip_horizontal") == True)

    # Get difference between p1 and p2.
    

if (__name__ == "__main__"):
    test_parameters()
    

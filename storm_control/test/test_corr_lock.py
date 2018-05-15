#!/usr/bin/env python
"""
Test correlation focus lock fitting.
"""
import numpy
import random

import storm_analysis.simulator.draw_gaussians_c as dg

import storm_control.sc_hardware.utility.corr_lock_c2dg as clf

def test_cl_1():

    sigma = 2.0
    cl_fit = clf.CorrLockFitter(roi_size = 8,
                                sigma = sigma,
                                threshold = 10)
    im_size = (50, 200)
    reps = 10

    # Test
    for i in range(reps):
        tx = 0.5 * im_size[0] + random.uniform(-5.0,5.0)
        ty = 0.5 * im_size[1] + random.uniform(-5.0,5.0)

        image = dg.drawGaussiansXY(im_size,
                                   numpy.array([tx]),
                                   numpy.array([ty]),
                                   sigma = sigma,
                                   height = 50.0)
    
        [mx, my, success] = cl_fit.findFitPeak(image)
        assert success
        assert (numpy.abs(mx-tx) < 1.0e-2)
        assert (numpy.abs(my-ty) < 1.0e-2)

    cl_fit.cleanup()


if (__name__ == "__main__"):
    test_cl_1()
    

#!/usr/bin/env python
"""
Test correlation lock.

Hazen 09/19
"""
import numpy

import storm_analysis.simulator.draw_gaussians_c as dg

import storm_control.sc_hardware.utility.corr_lock_c2dg as cl2DG


def test_c2dg():
    clf = cl2DG.CorrLockFitter(roi_size = 8, sigma = 1.0, threshold = 0.1)
    for i in range(10):
        x = float(i/10.0)
        image1 = dg.drawGaussiansXY((50,200),
                                    numpy.array([25 + x]),
                                    numpy.array([124 + x + 0.2]))
        [ox, oy, success] = clf.findFitPeak(image1)
        assert(success)
        assert(numpy.allclose(numpy.array([ox,oy]),
                              numpy.array([25.0 + x, 124 + x + 0.2]),
                              atol = 1.0e-3,
                              rtol = 1.0e-3))

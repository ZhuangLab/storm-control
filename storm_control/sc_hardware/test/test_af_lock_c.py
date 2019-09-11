#!/usr/bin/env python
"""
Test autofocus lock.

Hazen 09/19
"""
import numpy
import random

import storm_analysis.simulator.draw_gaussians_c as dg

import storm_control.sc_hardware.utility.af_lock_c as afLC


def test_afLC():
    afc = afLC.AFLockPy(offset = 0.0)

    cx = 16.0
    cy = 32.0

    for i in range(10):
        x_off = 4.0 * (random.random() - 0.5)
        y_off = 4.0 * (random.random() - 0.5)
    
        x1_off = cx + 0.5*x_off
        y1_off = cy + 0.5*y_off
        
        x2_off = 2.0*cx - x1_off
        y2_off = 2.0*cy - y1_off
        
        im1 = dg.drawGaussiansXY((32,64), numpy.array([x1_off]), numpy.array([y1_off]))
        im2 = dg.drawGaussiansXY((32,64), numpy.array([x2_off]), numpy.array([y2_off]))
        
        [dx, dy, success, mag] = afc.findOffset(im1, im2)

        assert(numpy.allclose(numpy.array([dx, dy]),
                              numpy.array([x_off, y_off]),
                              atol = 1.0e-3,
                              rtol = 1.0e-3))



if (__name__ == "__main__"):
    test_afLC()

    

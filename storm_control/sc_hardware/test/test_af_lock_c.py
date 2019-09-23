#!/usr/bin/env python
"""
Test autofocus lock.

Hazen 09/19
"""
import numpy
import random

import storm_analysis.simulator.draw_gaussians_c as dg

import storm_control.sc_hardware.utility.af_lock_c as afLC


# 2D Python version.
def test_afLCPy():
    afc = afLC.AFLockPy(offset = 0.0)

    cx = 16.0
    cy = 32.0

    for i in range(10):
        x1_off = cx + 10.0 * (random.random() - 0.5)
        y1_off = cy + 40.0 * (random.random() - 0.5)

        x2_off = cx + 10.0 * (random.random() - 0.5)
        y2_off = cy + 40.0 * (random.random() - 0.5)
        
        im1 = dg.drawGaussiansXY((32,64), numpy.array([x1_off]), numpy.array([y1_off]))
        im2 = dg.drawGaussiansXY((32,64), numpy.array([x2_off]), numpy.array([y2_off]))
        
        [dx, dy, res, mag] = afc.findOffset(im1, im2)

        assert(res.success)
        assert(numpy.allclose(numpy.array([dx, dy]),
                              numpy.array([x1_off - x2_off, y1_off - y2_off]),
                              atol = 1.0e-3,
                              rtol = 1.0e-3))
        

# 1D Python version.
def test_afLCPy1D():
    afc = afLC.AFLockPy1D(offset = 0.0)

    cx = 2.0
    cy = 32.0

    for i in range(10):
        x1_off = cx
        y1_off = cy + 40.0 * (random.random() - 0.5)

        x2_off = cx
        y2_off = cy + 40.0 * (random.random() - 0.5)
        
        im1 = dg.drawGaussiansXY((4,64), numpy.array([x1_off]), numpy.array([y1_off]))
        im2 = dg.drawGaussiansXY((4,64), numpy.array([x2_off]), numpy.array([y2_off]))
        
        [dx, dy, res, mag] = afc.findOffset(im1, im2)

        assert(res.success)
        assert(numpy.allclose(numpy.array([dx, dy]),
                              numpy.array([x1_off - x2_off, y1_off - y2_off]),
                              atol = 1.0e-3,
                              rtol = 1.0e-3))

        
# 2D C Version, test that initial offset estimate is correct.
def test_afLC_offset():
    afc = afLC.AFLockC(offset = 0.0)

    cx = 16.0
    cy = 32.0

    for i in range(10):
        x1_off = cx + random.randint(-5, 5)
        y1_off = cy + random.randint(-20, 20)

        x2_off = cx + random.randint(-5, 5)
        y2_off = cy + random.randint(-20, 20)
        
        im1 = dg.drawGaussiansXY((32,64), numpy.array([x1_off]), numpy.array([y1_off]))
        im2 = dg.drawGaussiansXY((32,64), numpy.array([x2_off]), numpy.array([y2_off]))

        afc.findOffset(im1, im2)
        offset = afc.getOffset()
        assert(numpy.allclose(offset, numpy.array([x1_off - x2_off, y1_off - y2_off])))
        

if (__name__ == "__main__"):
    test_afLC_offset()


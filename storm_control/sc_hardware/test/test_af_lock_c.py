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

        
# 2D C Version (Python solver), test that initial offset estimate is correct.
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


# 2D C version (Python solver).
def test_afLC():
    afc = afLC.AFLockC(offset = 0.0)

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


# 2D C version, downsampled (Python solver).
def test_afLC_ds():
    downsample = 4
    afc = afLC.AFLockC(offset = 0.0, downsample = downsample)

    cx = 32.0
    cy = 64.0

    for i in range(10):
        x1_off = cx + 10.0 * (random.random() - 0.5)
        y1_off = cy + 40.0 * (random.random() - 0.5)

        x2_off = cx + 10.0 * (random.random() - 0.5)
        y2_off = cy + 40.0 * (random.random() - 0.5)
        
        im1 = dg.drawGaussiansXY((64,128), numpy.array([x1_off]), numpy.array([y1_off]), sigma = downsample)
        im2 = dg.drawGaussiansXY((64,128), numpy.array([x2_off]), numpy.array([y2_off]), sigma = downsample)
        
        [dx, dy, res, mag] = afc.findOffset(im1, im2)
        
        assert(res.success)
        assert(numpy.allclose(numpy.array([downsample*dx, downsample*dy]),
                              numpy.array([x1_off - x2_off, y1_off - y2_off]),
                              atol = 1.0e-2,
                              rtol = 1.0e-2))
        

# 2D C version, downsampled, combined uint16 image. (Python solver).
def test_afLC_ds_u16():
    downsample = 4
    afc = afLC.AFLockC(offset = 0.0, downsample = downsample)

    cx = 32.0
    cy = 64.0

    for i in range(10):
        x1_off = cx + 10.0 * (random.random() - 0.5)
        y1_off = cy + 40.0 * (random.random() - 0.5)

        x2_off = 3*cx + 10.0 * (random.random() - 0.5)
        y2_off = cy + 40.0 * (random.random() - 0.5)
        
        im = dg.drawGaussiansXY((128,128),
                                numpy.array([x1_off, x2_off]),
                                numpy.array([y1_off, y2_off]),
                                sigma = downsample)
        im = (100.0*im).astype(numpy.uint16)
        
        [dx, dy, res, mag] = afc.findOffsetU16(im)

        if not res.success:
            if (res.status != 2):
                assert False, "Fitting failed " + res.message
        assert(numpy.allclose(numpy.array([downsample*dx, downsample*dy]),
                              numpy.array([x1_off - x2_off + 2.0*cx, y1_off - y2_off]),
                              atol = 1.0e-2,
                              rtol = 1.0e-2))

        
# Test gradient calculation.
def test_grad():
    dx = 1.0e-6
    
    afc_py = afLC.AFLockPy(offset = 0.0)
    afc = afLC.AFLockC(offset = 0.0)

    x1_off = 8.0
    y1_off = 16.0
    x2_off = 8.0
    y2_off = 16.0
        
    im1 = dg.drawGaussiansXY((32,64), numpy.array([x1_off]), numpy.array([y1_off]))
    im2 = dg.drawGaussiansXY((32,64), numpy.array([x2_off]), numpy.array([y2_off]))

    # Initialize fitter.
    afc_py.findOffset(im1, im2)
    afc.findOffset(im1, im2)

    for i in range(10):
        v1 = numpy.random.normal(size = 2)

        # Exact.
        gce_py = afc_py.gradCost(v1)
        gce_c = afc.gradCost(v1)

        # Analytic.
        gca = numpy.zeros(2)
    
        v2 = numpy.copy(v1)
        v2[0] += dx
        gca[0] = (afc_py.cost(v2) - afc_py.cost(v1))/dx
        
        v2 = numpy.copy(v1)
        v2[1] += dx
        gca[1] = (afc_py.cost(v2) - afc_py.cost(v1))/dx

        assert(numpy.allclose(gca, gce_py, atol = 1.0e-4, rtol = 1.0e-4))
        assert(numpy.allclose(gca, gce_c, atol = 1.0e-4, rtol = 1.0e-4))
        
        
# Test hessian calculation.
def test_hess():
    dx = 1.0e-6
    
    afc_py = afLC.AFLockPy(offset = 0.0)
    afc = afLC.AFLockC(offset = 0.0)

    x1_off = 8.0
    y1_off = 16.0
    x2_off = 8.0
    y2_off = 16.0
        
    im1 = dg.drawGaussiansXY((32,64), numpy.array([x1_off]), numpy.array([y1_off]))
    im2 = dg.drawGaussiansXY((32,64), numpy.array([x2_off]), numpy.array([y2_off]))

    # Initialize fitter.
    afc_py.findOffset(im1, im2)
    afc.findOffset(im1, im2)

    for i in range(10):
        v1 = numpy.random.normal(size = 2)

        # Exact.
        hce_py = afc_py.hessCost(v1)
        hce_c = afc.hessCost(v1)

        # Analytic.
        hca = numpy.zeros((2,2))
    
        v2 = numpy.copy(v1)
        v2[0] += dx
        hca[0,:] = (afc_py.gradCost(v2) - afc_py.gradCost(v1))/dx
        
        v2 = numpy.copy(v1)
        v2[1] += dx
        hca[1,:] = (afc_py.gradCost(v2) - afc_py.gradCost(v1))/dx
        
        assert(numpy.allclose(hca, hce_py, atol = 1.0e-3, rtol = 1.0e-3))
        assert(numpy.allclose(hca, hce_c, atol = 1.0e-3, rtol = 1.0e-3))
        

        
if (__name__ == "__main__"):
    test_hess()

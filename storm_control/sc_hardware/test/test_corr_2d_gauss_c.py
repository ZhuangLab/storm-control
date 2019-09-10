#!/usr/bin/env python
"""
Unit tests for corr_2d_gauss_c

Hazen 09/19
"""
import numpy

import storm_control.sc_hardware.utility.corr_2d_gauss_c as corr2DGauss


def test_xy_derivatives():
    im_size = (9,9)
    c2dg_py = corr2DGauss.Corr2DGaussPy(size = im_size, sigma = 1.0)

    x = numpy.zeros(2)
    image = c2dg_py.translate(x)
    c2dg_py.setImage(image)
        
    x = numpy.zeros(2)
    dx = 1.0e-6
    
    # Check X derivative.
    for i in range(-3,4):
        offset = 0.1 * i
        x[0] = offset + dx
        f1 = c2dg_py.func(x)
        x[0] = offset
        f2 = c2dg_py.func(x)
        assert(abs((f1-f2)/dx - c2dg_py.dx(x)) < 1.0e-4)

    # Check Y derivative.
    for i in range(-3,4):
        offset = 0.1 * i
        x[1] = offset + dx
        f1 = c2dg_py.func(x)
        x[1] = offset
        f2 = c2dg_py.func(x)
        assert(abs((f1-f2)/dx - c2dg_py.dy(x)) < 1.0e-4)


def test_xy_2nd_derivatives():

    # Test X/Y second derivatives.
    im_size = (9,9)
    c2dg_py = corr2DGauss.Corr2DGaussPy(size = im_size, sigma = 1.0)

    x = numpy.zeros(2)
    image = c2dg_py.translate(x)
    c2dg_py.setImage(image)
        
    dx = 1.0e-6

    # Check X second derivative.
    x = numpy.zeros(2)
    for i in range(-3,4):
        offset = 0.1 * i + 0.05
        x[0] = offset + dx
        f1 = c2dg_py.func(x)
        x[0] = offset
        f2 = c2dg_py.func(x)
        x[0] = offset - dx        
        f3 = c2dg_py.func(x)
        x[0] = offset
        nddx = (f1 - 2.0 * f2 + f3)/(dx*dx)
        assert(abs(nddx - c2dg_py.ddx(x)) < 0.02)

    # Check Y second derivative.
    x = numpy.zeros(2)
    for i in range(-3,4):
        offset = 0.1 * i + 0.05
        x[1] = offset + dx
        f1 = c2dg_py.func(x)
        x[1] = offset
        f2 = c2dg_py.func(x)
        x[1] = offset - dx        
        f3 = c2dg_py.func(x)
        x[1] = offset
        nddy = (f1 - 2.0 * f2 + f3)/(dx*dx)
        assert(abs(nddy - c2dg_py.ddy(x)) < 0.02)


def test_offset_python():

    # Test finding the correct offset (Python version).
    im_size = (9,9)
    c2dg_py = corr2DGauss.Corr2DGaussPyNCG(size = im_size, sigma = 1.0)

    for i in range(-2,3):
        disp = numpy.array([0.1*i, -0.2*i])
        image = c2dg_py.translate(disp)
        c2dg_py.setImage(image)
        [dd, success, fn, status] = c2dg_py.maximize()
        assert(success)
        assert(numpy.allclose(dd, disp, atol = 1.0e-3, rtol = 1.0e-3))
        

def test_c_vs_python():
    
    # Test C version against Python version.
    im_size = (9,10)
    c2dg_py = corr2DGauss.Corr2DGaussPy(size = im_size, sigma = 1.0)
    c2dg_c = corr2DGauss.Corr2DGaussC(size = im_size, sigma = 1.0)

    x = numpy.zeros(2)
    image = c2dg_py.translate(x)
        
    c2dg_py.setImage(image)
    c2dg_c.setImage(image)

    assert(abs(c2dg_py.func(x) - c2dg_c.func(x)) < 1.0e-6)
    
    x = numpy.zeros(2)        
    for i in range(-3,4):
        x[0] = 0.1*i
        assert(abs(c2dg_py.dx(x) - c2dg_c.dx(x)) < 1.0e-6)

    x = numpy.zeros(2)
    for i in range(-3,4):
        x[1] = 0.1*i
        assert(abs(c2dg_py.dy(x) - c2dg_c.dy(x)) < 1.0e-6)

    x = numpy.zeros(2)
    for i in range(-3,4):
        x[1] = 0.1*i
        assert(abs(c2dg_py.ddx(x) - c2dg_c.ddx(x)) < 1.0e-6)

    x = numpy.zeros(2)
    for i in range(-3,4):
        x[1] = 0.1*i
        assert(abs(c2dg_py.ddy(x) - c2dg_c.ddy(x)) < 1.0e-6)


def test_offset_c():

    # Test finding the correct offset (C version).
    im_size = (9,9)
    c2dg_c = corr2DGauss.Corr2DGaussCNCG(size = im_size, sigma = 1.0)
    c2dg_py = corr2DGauss.Corr2DGaussPyNCG(size = im_size, sigma = 1.0)

    for i in range(-2,3):
        disp = numpy.array([0.1*i, -0.2*i])
        image = c2dg_py.translate(disp)
        c2dg_c.setImage(image)
        [dd, success, fn, status] = c2dg_c.maximize()
        assert(success)
        assert(numpy.allclose(dd, disp, atol = 1.0e-3, rtol = 1.0e-3))

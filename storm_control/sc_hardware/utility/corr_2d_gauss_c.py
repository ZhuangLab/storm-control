#!/usr/bin/env python
"""
Fitting for offset using correlation with a 2D Gaussian.

Hazen 04/18
"""
import ctypes
import numpy
from numpy.ctypeslib import ndpointer
import scipy
import scipy.optimize

import storm_analysis.simulator.draw_gaussians_c as dg

import storm_control.c_libraries.loadclib as loadclib


# Load C library.
c2dg = loadclib.loadCLibrary("corr_2d_gauss")

# corr2DData structure definition.
class corr2DData(ctypes.Structure):
    _fields_ = [('n_checks', ctypes.c_int),
                ('n_updates', ctypes.c_int),
                
                ('size_x', ctypes.c_int),
                ('size_y', ctypes.c_int),
                
                ('stale_ddx', ctypes.c_int),
                ('stale_ddy', ctypes.c_int),
                ('stale_dx', ctypes.c_int),
                ('stale_dy', ctypes.c_int),
                ('stale_f', ctypes.c_int),
                ('stale_gi', ctypes.c_int),
                
                ('cx', ctypes.c_double),
                ('cy', ctypes.c_double),
                ('ddx', ctypes.c_double),
                ('ddy', ctypes.c_double),
                ('dx', ctypes.c_double),
                ('dy', ctypes.c_double),
                ('f', ctypes.c_double),
                ('last_x', ctypes.c_double),
                ('last_y', ctypes.c_double),
                ('sg_term', ctypes.c_double),
                
                ('g_im', ctypes.POINTER(ctypes.c_double)),
                ('gx', ctypes.POINTER(ctypes.c_double)),
                ('gy', ctypes.POINTER(ctypes.c_double)),
                ('r_im', ctypes.POINTER(ctypes.c_double)),
                ('xi', ctypes.POINTER(ctypes.c_double)),
                ('yi', ctypes.POINTER(ctypes.c_double))]

# C interface definition.
c2dg.cleanup.argtypes = [ctypes.POINTER(corr2DData)]

c2dg.ddx.argtypes = [ctypes.POINTER(corr2DData),
                     ctypes.c_double,
                     ctypes.c_double]
c2dg.ddx.restype = ctypes.c_double

c2dg.ddy.argtypes = [ctypes.POINTER(corr2DData),
                     ctypes.c_double,
                     ctypes.c_double]
c2dg.ddy.restype = ctypes.c_double

c2dg.dx.argtypes = [ctypes.POINTER(corr2DData),
                    ctypes.c_double,
                    ctypes.c_double]
c2dg.dx.restype = ctypes.c_double

c2dg.dy.argtypes = [ctypes.POINTER(corr2DData),
                    ctypes.c_double,
                    ctypes.c_double]
c2dg.dy.restype = ctypes.c_double

c2dg.fn.argtypes = [ctypes.POINTER(corr2DData),
                    ctypes.c_double,
                    ctypes.c_double]
c2dg.fn.restype = ctypes.c_double

c2dg.initialize.argtypes = [ctypes.c_double,
                            ctypes.c_int,
                            ctypes.c_int]
c2dg.initialize.restype = ctypes.POINTER(corr2DData)

c2dg.setImage.argtypes = [ctypes.POINTER(corr2DData),
                          ndpointer(dtype=numpy.float64)]


class Corr2DGaussC(object):
    """
    This class optimizes the correlation between an image and a 2D
    Gaussian.

    C library wrapper implementation.
    """
    def __init__(self, size = None, sigma = None, verbose = True, **kwds):
        super(Corr2DGaussC, self).__init__(**kwds)
                
        assert(len(size) == 2), "Size must have two elements."

        self.verbose = verbose
        self.x_size = size[0]
        self.y_size = size[1]
        
        self.c2d = c2dg.initialize(sigma, size[0], size[1])
        
    def cleanup(self):
        if self.verbose:
            print("Lock fitting: {0:0d} checks, {1:0d} updates".format(self.c2d.contents.n_checks,
                                                                       self.c2d.contents.n_updates))
        c2dg.cleanup(self.c2d)
        self.c2d = None

    def ddx(self, x):
        return c2dg.ddx(self.c2d, x[0], x[1])

    def ddy(self, x):
        return c2dg.ddy(self.c2d, x[0], x[1])

    def dx(self, x):
        return c2dg.dx(self.c2d, x[0], x[1])

    def dy(self, x):
        return c2dg.dy(self.c2d, x[0], x[1])    

    def func(self, x, sign = 1.0):
        return sign * c2dg.fn(self.c2d, x[0], x[1])

    def hessian(self, x, sign = 1.0):
        dxdy = -sign * self.dx(x) * self.dy(x)
        return numpy.array([[sign * self.ddx(x), dxdy],
                            [dxdy, sign * self.ddy(x)]])
            
    def jacobian(self, x, sign = 1.0):
        return sign * numpy.array([self.dx(x), self.dy(x)])

    def setImage(self, image):
        assert(image.shape[0] == self.x_size)
        assert(image.shape[1] == self.y_size)

        c_image = numpy.ascontiguousarray(image, dtype = numpy.float64)
        c2dg.setImage(self.c2d, c_image)
    

class Corr2DGaussPy(object):
    """
    This class optimizes the correlation between an image and a 2D
    Gaussian.

    Python implementation.
    """
    def __init__(self, size = None, sigma = None):
        """
        size - The size of the image.
        sigma - The sigma of the Gaussian.
        """
        super(Corr2DGaussPy, self).__init__()
        
        assert(len(size) == 2), "Size must have two elements."

        self.g_image = None
        self.g_x = None
        self.image = None
        self.sigma = sigma
        self.x_size = size[0]
        self.y_size = size[1]

        [self.xi,self.yi] = numpy.mgrid[-self.x_size/2.0:self.x_size/2.0,
                                        -self.y_size/2.0:self.y_size/2.0]

        self.xi += 0.5
        self.yi += 0.5
        
        self.cx = 0.5 * self.x_size - 0.5
        self.cy = 0.5 * self.y_size - 0.5

    def cleanup(self):
        pass

    def ddx(self, x, sign = 1.0):
        g_image = self.translate(x)
        t1 = (x[0] - self.xi)/(self.sigma*self.sigma)
        t2 = 1.0/(self.sigma * self.sigma)
        return sign * numpy.sum(self.image * g_image * (t1*t1 - t2))

    def ddy(self, x, sign = 1.0):
        g_image = self.translate(x)
        t1 = (x[1] - self.yi)/(self.sigma*self.sigma)
        t2 = 1.0/(self.sigma * self.sigma)
        return sign * numpy.sum(self.image * g_image * (t1*t1 - t2))
    
    def dx(self, x, sign = 1.0):
        g_image = self.translate(x)
        t1 = -(x[0] - self.xi)/(self.sigma*self.sigma)
        return sign * numpy.sum(self.image * g_image * t1)

    def dy(self, x, sign = 1.0):
        g_image = self.translate(x)
        t1 = -(x[1] - self.yi)/(self.sigma*self.sigma)
        return sign * numpy.sum(self.image * g_image * t1)

    def func(self, x, sign = 1.0):
        g_image = self.translate(x)
        return sign * numpy.sum(self.image * g_image)

    def hessian(self, x, sign = 1.0):
        dxdy = -sign * self.dx(x) * self.dy(x)
        return numpy.array([[sign * self.ddx(x), dxdy],
                            [dxdy, sign * self.ddy(x)]])
            
    def jacobian(self, x, sign = 1.0):
        return sign * numpy.array([self.dx(x), self.dy(x)])
        
    def setImage(self, image):
        assert(image.shape[0] == self.x_size)
        assert(image.shape[1] == self.y_size)

        self.g_image = None
        self.image = image

    def translate(self, x):
        
        if (self.g_image is None) or (not numpy.allclose(self.g_x, x, atol = 1.0e-12, rtol = 1.0e-12)):
            self.g_image = dg.drawGaussiansXY((self.x_size, self.y_size),
                                              numpy.array([self.cx + x[0]]),
                                              numpy.array([self.cy + x[1]]),
                                              sigma = self.sigma)
            self.g_x = numpy.copy(x)

        return self.g_image


class Corr2DGaussPyLM(Corr2DGaussPy):
    """
    Optimize using a variant of the Levenberg-Marquadt algorithm.
    """
    def __init__(self, max_reps = 100, tolerance = 1.0e-6, **kwds):
        super(Corr2DGaussPyLM, self).__init__(**kwds)

        self.fn_curr = None
        self.fn_old = None
        self.lm_lambda = 1.0
        self.max_reps = max_reps
        self.tolerance = tolerance
        
    def hasConverged(self):
        return (abs((self.fn_old - self.fn_curr)/self.fn_curr) < self.tolerance)

    def update(self, x):
        """
        Return the update vector at x.
        """
        jac = self.jacobian(x, sign = -1.0)
        hess = self.hessian(x, sign = -1.0)
        for i in range(jac.size):
            hess[i,i] += hess[i,i] * self.lm_lambda
        delta = numpy.linalg.solve(hess, jac)
        return delta

    def maximize(self, dx = 0.0, dy = 0.0):
        self.lm_lambda = 1.0
        xo = numpy.array([dx, dy])

        self.fn_curr = self.func(xo, sign = -1.0)
        for i in range(self.max_reps):
            xn = xo - self.update(xo)
            fn = self.func(xn, sign = -1.0)

            # If we did not improve increase lambda and try again.
            if (fn > self.fn_curr):
                self.lm_lambda = 2.0 * self.lm_lambda
                continue

            self.lm_lambda = 0.9 * self.lm_lambda
            self.fn_old = self.fn_curr
            self.fn_curr = fn
            xo = xn
                
            if self.hasConverged():
                break

        success = (i < (self.max_reps - 1))
        return [xo, success, -self.fn_curr, 0]


class Corr2DGaussCNCG(Corr2DGaussC):
    """
    Optimize using Newton-CG (Python version).
    """
    def maximize(self, dx = 0.0, dy = 0.0):
        """
        Find the offset that optimizes the correlation of the 
        Gaussian with the reference image.
        """
        x0 = numpy.array([dx, dy])

        fit = scipy.optimize.minimize(self.func,
                                      x0,
                                      args=(-1.0,),
                                      method='Newton-CG',
                                      jac=self.jacobian,
                                      hess=self.hessian,
                                      options={'xtol': 1e-3, 'disp': False})

        if (not fit.success) and (not (fit.status == 2)):
        #if (not fit.success):
            print("Maximization failed with:")
            print(fit.message)
            print("Status:", fit.status)
            print("X:", fit.x)
            print("Function value:", -fit.fun)
            print()
                        
        return [fit.x, fit.success, -fit.fun, fit.status]


class Corr2DGaussPyNCG(Corr2DGaussPy):
    """
    Optimize using Newton-CG (Python version).
    """
    def maximize(self, dx = 0.0, dy = 0.0):
        """
        Find the offset that optimizes the correlation of the 
        Gaussian with the reference image.
        """
        x0 = numpy.array([dx, dy])

        fit = scipy.optimize.minimize(self.func,
                                      x0,
                                      args=(-1.0,),
                                      method='Newton-CG',
                                      jac=self.jacobian,
                                      hess=self.hessian,
                                      options={'xtol': 1e-3, 'disp': False})

        if (not fit.success) and (not (fit.status == 2)):
        #if (not fit.success):
            print("Maximization failed with:")
            print(fit.message)
            print("Status:", fit.status)
            print("X:", fit.x)
            print("Function value:", -fit.fun)
            print()
                        
        return [fit.x, fit.success, -fit.fun, fit.status]    


#       
# The MIT License
#
# Copyright (c) 2018 Babcock Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

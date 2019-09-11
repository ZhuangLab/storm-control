#!/usr/bin/env python
"""
Fitting for offset using the autofocus lock.

Hazen 09/19
"""
import ctypes
import numpy
from numpy.ctypeslib import ndpointer
import scipy
import scipy.optimize

import storm_control.c_libraries.loadclib as loadclib


class AFLockPy(object):
    """
    The Python reference version of the autofocus lock function.
    """
    def __init__(self, offset = 0.0, **kwds):
        super().__init__(**kwds)

        self.im1 = None
        self.im1_fft = None
        self.im2_fft = None
        self.offset = offset
        self.x0 = None
        self.x_shift = None
        self.y0 = None
        self.y_shift = None

    def cost(self, p):
        tmp = self.im2_fft * numpy.exp(-self.x_shift*p[0]) * numpy.exp(-self.y_shift*p[1])
        im2_shift = numpy.real(numpy.fft.ifft2(tmp))
        return -numpy.sum(self.im1 * im2_shift)

    def findOffset(self, image1, image2):
        self.initialize(image1, image2)

        # Offset to the nearest pixel.
        [offset, mag] = self.pixelOffset()

        # Determine offset at the sub-pixel level.
        #
        # This is I think the best optimizer for this purpose.
        #
        p0 = numpy.array([0.0, 0.0])
        res = scipy.optimize.minimize(self.cost, p0, method = 'CG', jac = self.gradCost)

        offset += res.x
        return [offset[0], offset[1], res.success, mag]

    def gradCost(self, p):
        tmp = self.im2_fft * numpy.exp(-self.x_shift*p[0]) * numpy.exp(-self.y_shift*p[1])

        ft_dx = numpy.fft.ifft2(tmp * -self.x_shift)
        s_dx = -numpy.sum(self.im1 * numpy.real(ft_dx))

        ft_dy = numpy.fft.ifft2(tmp * -self.y_shift)
        s_dy = -numpy.sum(self.im1 * numpy.real(ft_dy))

        return numpy.array([s_dx, s_dy])

    def initialize(self, image1, image2):

        assert(image1.shape[0] == image2.shape[0])
        assert(image1.shape[1] == image2.shape[1])

        image1 = image1.astype(numpy.float) - self.offset
        image2 = image2.astype(numpy.float) - self.offset
        
        self.im1 = numpy.pad(image1, [[0, image1.shape[0]], [0, image1.shape[1]]], 'constant')
        self.im1_fft = numpy.fft.fft2(self.im1)

        im2 = numpy.flipud(numpy.fliplr(image2))
        im2 = numpy.pad(image2, [[0, image1.shape[0]], [0, image1.shape[1]]], 'constant')
        self.im2_fft = numpy.fft.fft2(im2)
                             
        if self.x_shift is None:
            x_freq = numpy.repeat(numpy.fft.fftfreq(im2.shape[0])[:, numpy.newaxis], im2.shape[1], axis = 1)
            y_freq = numpy.repeat(numpy.fft.fftfreq(im2.shape[1])[numpy.newaxis, :], im2.shape[0], axis = 0)

            self.x_shift = 1j * 2.0 * numpy.pi * x_freq
            self.y_shift = 1j * 2.0 * numpy.pi * y_freq

            self.x0 = image1.shape[0]
            self.y0 = image1.shape[1]
            
        else:
            assert(self.im1.shape[0] == self.x_shift.shape[0])
            assert(self.im1.shape[1] == self.x_shift.shape[1])

    def pixelOffset(self):
        conv = numpy.real(numpy.fft.ifft2(self.im1_fft * self.im2_fft))
        [ix, iy] = numpy.unravel_index(conv.argmax(), conv.shape)
        return [numpy.array([ix - self.x0, iy - self.y0], dtype = numpy.float), conv[ix,iy]]


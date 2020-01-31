#!/usr/bin/env python
"""
Fitting for offset using the autofocus lock.

Hazen 09/19
"""
import ctypes
import numpy
from numpy.ctypeslib import ndpointer
import scipy
import scipy.misc
import scipy.optimize

import storm_control.c_libraries.loadclib as loadclib


# Load C library.
af = loadclib.loadCLibrary("af_lock")


#
# The Python definitions of the C structure in af_lock.c
#
class afLockData(ctypes.Structure):
    _fields_ = [('downsample', ctypes.c_int),
                ('fft_size', ctypes.c_int),
                ('xo', ctypes.c_int),
                ('x_size', ctypes.c_int),
                ('yo', ctypes.c_int),
                ('y_size', ctypes.c_int),

                ('cost', ctypes.c_double),
                ('dx', ctypes.c_double),
                ('dy', ctypes.c_double),
                ('mag', ctypes.c_double),
                ('norm', ctypes.c_double),

                ('cost_grad', ctypes.POINTER(ctypes.c_double)),
                ('cost_hess', ctypes.POINTER(ctypes.c_double)),
                ('fft_vector', ctypes.POINTER(ctypes.c_double)),
                ('im1', ctypes.POINTER(ctypes.c_double)),
                ('w1', ctypes.POINTER(ctypes.c_double)),
                ('x_shift', ctypes.POINTER(ctypes.c_double)),
                ('x_r', ctypes.POINTER(ctypes.c_double)),
                ('x_c', ctypes.POINTER(ctypes.c_double)),
                ('y_shift', ctypes.POINTER(ctypes.c_double)),
                ('y_r', ctypes.POINTER(ctypes.c_double)),
                ('y_c', ctypes.POINTER(ctypes.c_double)),

                ('fft_backward', ctypes.c_void_p),
                ('fft_forward', ctypes.c_void_p),

                # Techinically these are fftw_complex, so this might not be quite right.
                ('fft_vector_fft', ctypes.POINTER(ctypes.c_double)),
                ('im2_fft', ctypes.POINTER(ctypes.c_double)),
                ('im2_fft_shift', ctypes.POINTER(ctypes.c_double))]

    
# C interface definition.
af.aflCalcShift.argtypes = [ctypes.POINTER(afLockData)]

af.aflCleanup.argtypes = [ctypes.POINTER(afLockData)]

af.aflCost.argtypes = [ctypes.POINTER(afLockData),
                       ctypes.c_double,
                       ctypes.c_double]

af.aflCostGradient.argtypes = [ctypes.POINTER(afLockData),
                               ctypes.c_double,
                               ctypes.c_double]

af.aflCostHessian.argtypes = [ctypes.POINTER(afLockData),
                              ctypes.c_double,
                              ctypes.c_double]

af.aflGetCost.argtypes = [ctypes.POINTER(afLockData),
                          ndpointer(dtype=numpy.float64)]

af.aflGetCostGradient.argtypes = [ctypes.POINTER(afLockData),
                                  ndpointer(dtype=numpy.float64)]

af.aflGetCostHessian.argtypes = [ctypes.POINTER(afLockData),
                                 ndpointer(dtype=numpy.float64)]

af.aflGetMag.argtypes = [ctypes.POINTER(afLockData),
                         ndpointer(dtype=numpy.float64)]

af.aflGetOffset.argtypes = [ctypes.POINTER(afLockData),
                            ndpointer(dtype=numpy.float64)]

af.aflGetVector.argtypes = [ctypes.POINTER(afLockData),
                            ndpointer(dtype=numpy.float64),
                            ctypes.c_int]

af.aflInitialize.argtypes = [ctypes.c_int,
                             ctypes.c_int,
                             ctypes.c_int]
af.aflInitialize.restype = ctypes.POINTER(afLockData)

af.aflMinimizeNM.argtypes = [ctypes.POINTER(afLockData),
                             ctypes.c_double,
                             ctypes.c_int]
af.aflMinimizeNM.restype = ctypes.c_int

af.aflNewImage.argtypes = [ctypes.POINTER(afLockData),
                           ndpointer(dtype=numpy.float64),
                           ndpointer(dtype=numpy.float64),
                           ctypes.c_double,
                           ctypes.c_double]

af.aflNewImageU16.argtypes = [ctypes.POINTER(afLockData),
                              ndpointer(dtype=numpy.uint16),
                              ndpointer(dtype=numpy.uint16),
                              ctypes.c_double,
                              ctypes.c_double]

af.aflRebin.argtypes = [ctypes.POINTER(afLockData),
                        ndpointer(dtype=numpy.float64),
                        ctypes.c_double]

af.aflRebinU16.argtypes = [ctypes.POINTER(afLockData),
                           ndpointer(dtype=numpy.float64),
                           ctypes.c_double]

af.aflSolveStep.argtypes = [ctypes.POINTER(afLockData),
                            ndpointer(dtype=numpy.float64)]
af.aflSolveStep.restype = ctypes.c_int

    
class AFLockC(object):
    """
    The C version of the 2D autofocus lock function.
    """
    def __init__(self, downsample = 1, offset = 0.0, max_iters = 10, step_tol = 1.0e-6, **kwds):
        """
        offset - The background offset term.
        """
        super().__init__(**kwds)

        self.afld = None
        self.downsample = downsample
        self.im_x = None
        self.im_y = None
        self.max_iters = max_iters
        self.offset = offset
        self.step_tol = step_tol

    def cleanup(self):
        if self.afld is not None:
            af.aflCleanup(self.afld)
            self.afld = None

    def cost(self, p):
        af.aflCost(self.afld, p[0], p[1])
        cost = numpy.zeros(1, dtype = numpy.float64)
        af.aflGetCost(self.afld, cost)
        return cost[0]

    def findOffset(self, image1, image2):
        if self.afld is None:
            self.initialize(image1)

        assert (image1.shape[0] == self.im_x)
        assert (image1.shape[1] == self.im_y)
        assert (image2.shape[0] == self.im_x)
        assert (image2.shape[1] == self.im_y)

        # This function also determines the offset to the nearest pixel.
        af.aflNewImage(self.afld,
                       numpy.ascontiguousarray(image1, dtype = numpy.float64),
                       numpy.ascontiguousarray(image2, dtype = numpy.float64),
                       self.offset,
                       self.offset)

        mag = self.getMag()
        offset = self.getOffset()

        # Determine offset at the sub-pixel level.
        res = scipy.optimize.minimize(self.cost, offset, method = 'CG', jac = self.gradCost)

        return [res.x[0], res.x[1], res, mag]

    def findOffsetU16(self, image1, image2):
        """
        This version is designed for HAL. 'image1' and 'image2' should
        be of type numpy.uint16.
        """
        if self.afld is None:
            self.initialize(image1)

        assert (image1.shape[0] == self.im_x)
        assert (image1.shape[1] == self.im_y)
        assert (image2.shape[0] == self.im_x)
        assert (image2.shape[1] == self.im_y)

        # This function also determines the offset to the nearest pixel.
        af.aflNewImageU16(self.afld,
                          numpy.ascontiguousarray(image1, dtype = numpy.uint16),
                          numpy.ascontiguousarray(image2, dtype = numpy.uint16),
                          self.offset,
                          self.offset)

        mag = self.getMag()
        offset = self.getOffset()

        # Determine offset at the sub-pixel level.
        res = scipy.optimize.minimize(self.cost, offset, method = 'CG', jac = self.gradCost)

        return [res.x[0], res.x[1], res, mag]

    def findOffsetU16NM(self, image1, image2):
        """
        This version is designed for HAL. It uses Newton's method (implemented in
        C) to find the optimal offset.

        'image' should be a numpy.uint16 array containing both spots, one in the 
        top half of the image and the other in the bottom. The idea is to do the 
        type conversion and splitting in the C library for better performance.
        """
        if self.afld is None:
            self.initialize(image1)

        assert (image1.shape[0] == self.im_x)
        assert (image1.shape[1] == self.im_y)
        assert (image2.shape[0] == self.im_x)
        assert (image2.shape[1] == self.im_y)

        # This function also determines the offset to the nearest pixel.
        af.aflNewImageU16(self.afld,
                          numpy.ascontiguousarray(image1, dtype = numpy.uint16),
                          numpy.ascontiguousarray(image2, dtype = numpy.uint16),
                          self.offset,
                          self.offset)

        # Determine offset at the sub-pixel level.
        ret = af.aflMinimizeNM(self.afld, self.step_tol, self.max_iters)

        success = (ret == 0)
        if not success:
            print("C Newton solver failed with error code: ", ret)
           
        mag = self.getMag()
        offset = self.getOffset()

        return [offset[0], offset[1], success, mag]

    def gradCost(self, p):
        af.aflCostGradient(self.afld, p[0], p[1])
        grad = numpy.zeros(2, dtype = numpy.float64)
        af.aflGetCostGradient(self.afld, grad)
        return grad

    def getMag(self):
        mag = numpy.zeros(1, dtype = numpy.float64)
        af.aflGetMag(self.afld, mag)
        return mag[0]

    def getOffset(self):
        offset = numpy.ascontiguousarray(numpy.zeros(2, dtype = numpy.float64))
        af.aflGetOffset(self.afld, offset)
        return offset

    def getVector(self, which):
        sx = int(2*self.im_x/self.downsample)
        sy = int(2*self.im_y/self.downsample)
        vector = numpy.ascontiguousarray(numpy.zeros((sx, sy), dtype = numpy.float64))
        af.aflGetVector(self.afld, vector, which)
        return vector

    def hessCost(self, p):
        af.aflCostHessian(self.afld, p[0], p[1])
        hess = numpy.zeros((2,2), dtype = numpy.float64)
        af.aflGetCostHessian(self.afld, hess)
        return hess
    
    def initialize(self, image1):
        self.im_x = image1.shape[0]
        self.im_y = image1.shape[1]
        self.afld = af.aflInitialize(image1.shape[0], image1.shape[1], self.downsample)

    def solveStep(self, p):
        """
        This is for testing the C function that calculates the
        update step given the current gradient and Hessian.
        """
        # Calculate gradient and Hessian at p.
        af.aflCostGradient(self.afld, p[0], p[1])
        af.aflCostHessian(self.afld, p[0], p[1])

        # Calculate step.
        step = numpy.zeros(2, dtype = numpy.float64)
        af.aflSolveStep(self.afld, step)
        return step

    
class AFLockPy(object):
    """
    The Python reference version of the 2D autofocus lock function.
    """
    def __init__(self, offset = 0.0, **kwds):
        """
        offset - The background offset term.
        """
        super().__init__(**kwds)

        self.im1 = None
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
        [offset, mag] = self.pixelOffset(image2)

        # Determine offset at the sub-pixel level.
        #
        # This is I think the best optimizer for this purpose.
        #
        res = scipy.optimize.minimize(self.cost, offset, method = 'CG', jac = self.gradCost)

        return [res.x[0], res.x[1], res, mag]

    def gradCost(self, p):
        tmp = self.im2_fft * numpy.exp(-self.x_shift*p[0]) * numpy.exp(-self.y_shift*p[1])

        ft_dx = numpy.fft.ifft2(tmp * -self.x_shift)
        s_dx = -numpy.sum(self.im1 * numpy.real(ft_dx))

        ft_dy = numpy.fft.ifft2(tmp * -self.y_shift)
        s_dy = -numpy.sum(self.im1 * numpy.real(ft_dy))

        return numpy.array([s_dx, s_dy])

    def hessCost(self, p):
        tmp = self.im2_fft * numpy.exp(-self.x_shift*p[0]) * numpy.exp(-self.y_shift*p[1])

        hess = numpy.zeros((2,2))
        
        ft_dx_dx = numpy.fft.ifft2(tmp * self.x_shift * self.x_shift)
        hess[0,0] = -numpy.sum(self.im1 * numpy.real(ft_dx_dx))

        ft_dx_dy = numpy.fft.ifft2(tmp * self.x_shift * self.y_shift)
        hess[0,1] = -numpy.sum(self.im1 * numpy.real(ft_dx_dy))
        hess[1,0] = hess[0,1]
                
        ft_dy_dy = numpy.fft.ifft2(tmp * self.y_shift * self.y_shift)
        hess[1,1] = -numpy.sum(self.im1 * numpy.real(ft_dy_dy))

        return hess

    def initialize(self, image1, image2):

        assert(image1.shape[0] == image2.shape[0])
        assert(image1.shape[1] == image2.shape[1])

        image1 = image1.astype(numpy.float) - self.offset
        image2 = image2.astype(numpy.float) - self.offset
        
        self.im1 = numpy.pad(image1, [[0, image1.shape[0]], [0, image1.shape[1]]], 'constant')

        im2 = numpy.pad(image2, [[0, image2.shape[0]], [0, image2.shape[1]]], 'constant')
        self.im2_fft = numpy.fft.fft2(im2)
                             
        if self.x_shift is None:
            x_freq = numpy.repeat(numpy.fft.fftfreq(im2.shape[0])[:, numpy.newaxis], im2.shape[1], axis = 1)
            y_freq = numpy.repeat(numpy.fft.fftfreq(im2.shape[1])[numpy.newaxis, :], im2.shape[0], axis = 0)

            self.x_shift = 1j * 2.0 * numpy.pi * x_freq
            self.y_shift = 1j * 2.0 * numpy.pi * y_freq

            self.x0 = image1.shape[0] - 1
            self.y0 = image1.shape[1] - 1
            
        else:
            assert(self.im1.shape[0] == self.x_shift.shape[0])
            assert(self.im1.shape[1] == self.x_shift.shape[1])

    def pixelOffset(self, image2):
        im1_fft = numpy.fft.fft2(self.im1)
        
        im2 = numpy.flipud(numpy.fliplr(image2))
        im2 = numpy.pad(im2, [[0, im2.shape[0]], [0, im2.shape[1]]], 'constant')
        im2_fft = numpy.fft.fft2(im2) 

        conv = numpy.real(numpy.fft.ifft2(im1_fft*im2_fft))
        [ix, iy] = numpy.unravel_index(conv.argmax(), conv.shape)
        return [numpy.array([ix - self.x0, iy - self.y0], dtype = numpy.float), conv[ix,iy]]


class AFLockPy1D(object):
    """
    The Python reference version of the 1D autofocus lock function.

    This is not as stable as the 2D. The source of the transients isn't clear to
    me. It might be due issues getting the right baseline or maybe they come from
    the spots moving more then I expect in the transverse direction.
    """
    def __init__(self, offset = 0.0, **kwds):
        super().__init__(**kwds)

        self.im1 = None
        self.im2_fft = None
        self.offset = offset
        self.y0 = None
        self.y_shift = None

    def cost(self, p):
        tmp = self.im2_fft * numpy.exp(-self.y_shift*p[0])
        im2_shift = numpy.real(numpy.fft.ifft(tmp))
        return -numpy.sum(self.im1 * im2_shift)

    def findOffset(self, image1, image2):

        # Compress to 1D.
        image1 = image1.astype(numpy.float) - self.offset
        image1 = numpy.sum(image1, axis = 0)
        
        image2 = image2.astype(numpy.float) - self.offset
        image2 = numpy.sum(image2, axis = 0)

        # Initialize.
        self.initialize(image1, image2)

        # Offset to the nearest pixel.
        [offset, mag] = self.pixelOffset(image2)

        # Determine offset at the sub-pixel level.
        #
        # This is I think the best optimizer for this purpose.
        #
        res = scipy.optimize.minimize(self.cost, offset, method = 'CG', jac = self.gradCost)

        return [0.0, res.x[0], res, mag]

    def gradCost(self, p):
        tmp = self.im2_fft * numpy.exp(-self.y_shift*p[0])

        ft_dy = numpy.fft.ifft(tmp * -self.y_shift)
        s_dy = -numpy.sum(self.im1 * numpy.real(ft_dy))

        return numpy.array([s_dy])

    def initialize(self, image1, image2):

        assert(len(image1.shape) == 1)
        assert(len(image2.shape) == 1)
        assert(image1.size == image2.size)

        self.im1 = numpy.pad(image1, [0, image1.size], 'constant')

        im2 = numpy.pad(image2, [0, image2.size], 'constant')
        self.im2_fft = numpy.fft.fft(im2)
                             
        if self.y_shift is None:
            y_freq = numpy.fft.fftfreq(im2.size)

            self.y_shift = 1j * 2.0 * numpy.pi * y_freq

            self.y0 = image2.size - 1
            
        else:
            assert(self.im1.size == self.y_shift.size)

    def pixelOffset(self, image2):
        im1_fft = numpy.fft.fft(self.im1)
        
        im2 = numpy.flip(image2)
        im2 = numpy.pad(im2, [0, im2.size], 'constant')
        im2_fft = numpy.fft.fft(im2)

        conv = numpy.real(numpy.fft.ifft(im1_fft*im2_fft))
        iy = numpy.argmax(conv)
    
        return [numpy.array([iy - self.y0], dtype = numpy.float), conv[iy]]
    

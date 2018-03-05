#!/usr/bin/env python
"""
Python interface to the LMMoment object finder. This object finder
works by indentifying local maxima, then computing their first moment.

Note that the maximum number of objects found per image is limited to 1000.

Hazen 09/13
"""

import ctypes
import numpy
from numpy.ctypeslib import ndpointer
import os
import sys

import storm_control.c_libraries.loadclib as loadclib

lmmoment = False
max_locs = 1000


def cleanUp():
    """
    Called at program shutdown to free arrays allocated in C.
    """
    lmmoment.cleanup()


def initialize():
    """
    Called at program start up to allocate array and perform other
    initialization in C.
    """
    
    global lmmoment
    lmmoment = loadclib.loadCLibrary("LMMoment")

    lmmoment.initialize.argtypes = []
    lmmoment.cleanup.argtypes = []
    lmmoment.numberAndLocObjects.argtypes = [ndpointer(dtype=numpy.uint16),
                                             ctypes.c_int,
                                             ctypes.c_int,
                                             ctypes.c_int,
                                             ndpointer(dtype=numpy.float32),
                                             ndpointer(dtype=numpy.float32),
                                             ctypes.c_void_p]
    lmmoment.initialize()


def findObjects(frame, threshold):
    """
    Find the objects in the image.
    """
    x = numpy.zeros((max_locs), dtype = numpy.float32)
    y = numpy.zeros((max_locs), dtype = numpy.float32)
    n = ctypes.c_int(max_locs)
    lmmoment.numberAndLocObjects(numpy.ascontiguousarray(frame.getData(), dtype = numpy.uint16),
                                 frame.image_y,
                                 frame.image_x,
                                 threshold,
                                 x,
                                 y,
                                 ctypes.byref(n))
    return [x, y, n.value]


#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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

#!/usr/bin/python
#
## @file
#
# Python interface to the LMMoment object finder. This object finder
# works by indentifying local maxima, then computing their first moment.
#
# Note that the maximum number of objects found per image is limited to 1000.
#
# Hazen 09/13
#

from ctypes import *
import numpy
from numpy.ctypeslib import ndpointer
import os
import sys

lmmoment = False

max_locs = 1000

## cleanup
#
# Called at program shutdown to free arrays allocated in C.
#
def cleanup():
    lmmoment.cleanup()

## initialize
#
# Called at program start up to allocate array and perform other
# initialization in C.
#
def initialize():
    global lmmoment

    directory = os.path.dirname(__file__)
    if (directory == ""):
        directory = "./"
    else:
        directory += "/"

    if (sys.platform == "win32"):
        lmmoment = cdll.LoadLibrary(directory + "LMMoment.dll")
    else:
        lmmoment = cdll.LoadLibrary(directory + "LMMoment.so")

    lmmoment.initialize.argtypes = []
    lmmoment.cleanup.argtypes = []
    lmmoment.numberAndLocObjects.argtypes = [ndpointer(dtype=numpy.uint16),
                                             c_int,
                                             c_int,
                                             c_int,
                                             ndpointer(dtype=numpy.float32),
                                             ndpointer(dtype=numpy.float32),
                                             c_void_p]
    lmmoment.initialize()

## findObjects
#
# Find the objects in the image.
#
# @param np_image The image as a numpy.uint16 array.
# @param image_x The size of the image in x in pixels.
# @param image_y The size of the image in y in pixels.
# @param threshold The minimum height difference between the local maxima and the pixels on the edge of the peak.
#
# @return [[peak x positions], [peak y positions], number of peaks].
# 
def findObjects(np_image, image_x, image_y, threshold):
        x = numpy.zeros((max_locs), dtype = numpy.float32)
        y = numpy.zeros((max_locs), dtype = numpy.float32)
        n = c_int(max_locs)
        lmmoment.numberAndLocObjects(numpy.ascontiguousarray(np_image, dtype = numpy.uint16),
                                     image_y,
                                     image_x,
                                     threshold,
                                     x,
                                     y,
                                     byref(n))
        return [x, y, n.value]


# testing
if __name__ == "__main__":

    import numpy
    import time

    initialize()

    image_x = 1024
    image_y = 1024
    image = numpy.ones((image_x, image_y), dtype = numpy.uint16)

    repeats = 100
    start = time.time()
    for i in range(repeats):
        [x, y, n] = findObjects(image, image_x, image_y, 100)
        if ((i % 10) == 0):
            print i, n
    end = time.time()
    print "Time to process an image: ", ((end - start)/repeats), " seconds"

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

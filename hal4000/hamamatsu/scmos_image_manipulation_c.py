#!/usr/bin/python
#
## @file
#
# Python interface to the sCMOS image manipulation library. The library
# is used to speed up the rendering of the image in the UI. My experience
# was that for the largest images using numpy to do the image scaling
# and typy conversion was not fast enough.
#
# Hazen 10/13
# 

import ctypes
import math
import numpy
from numpy.ctypeslib import ndpointer
import os

directory = os.path.dirname(__file__)
if not (directory == ""):
    directory += "/"

image_manip = ctypes.cdll.LoadLibrary(directory + "scmos_image_manipulation.dll")

# C interface definition.
image_manip.rescaleImage.argtypes = [ndpointer(dtype=numpy.uint8),
                                     ndpointer(dtype=numpy.uint16),
                                     ctypes.c_int,
                                     ctypes.c_int,
                                     ctypes.c_int,
                                     ctypes.c_void_p,
                                     ctypes.c_void_p]

## rescaleImage
#
# This converts a uint16 image into a uint8 image based on the display
# range. As a side effect it also returns the minimum and maximum values
# in the image.
#
# @param image The original image as numpy.uint16 array.
# @param display_range [image value that equals 0, image value that equals 255].
#
# @return [numpy.uint8 image, original image minimum, original image maximum]
#
def rescaleImage(image, display_range):
    c_rescale = numpy.empty(image.shape, dtype = numpy.uint8)
    image_min = ctypes.c_int(0)
    image_max = ctypes.c_int(0)
    image_manip.rescaleImage(c_rescale,
                             image,
                             image.size,
                             display_range[0],
                             display_range[1],
                             ctypes.byref(image_min),
                             ctypes.byref(image_max))

    return [c_rescale, image_min.value, image_max.value]

# Testing
if __name__ == "__main__":
    image = numpy.ones((256,256), dtype = numpy.uint16)
    image[10,10] = 10
    [rs_image, image_min, image_max] = rescaleImage(image, [2, 9])
    print rs_image[0,0], rs_image[10,10], image_min, image_max

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

#!/usr/bin/python
#
## @file
#
# Python interface to the sCMOS image manipulation library. The library
# is used to speed up the rendering of the image in the UI. My experience
# was that for the largest images using numpy to do the image scaling
# and typy conversion was not fast enough.
#
# Hazen 09/15
# 

import ctypes
import math
import numpy
from numpy.ctypeslib import ndpointer
import os
import sys

directory = os.path.dirname(__file__)
if (directory == ""):
    directory = "./"
else:
    directory += "/"

if (sys.platform == "win32"):
    image_manip = ctypes.cdll.LoadLibrary(directory + "scmos_image_manipulation.dll")
else:
    image_manip = ctypes.cdll.LoadLibrary(directory + "scmos_image_manipulation.so")

# C interface definition.
rescale_fn_arg_types = [ndpointer(dtype=numpy.uint8),
                        ndpointer(dtype=numpy.uint16),
                        ctypes.c_int,
                        ctypes.c_int,
                        ctypes.c_int,
                        ctypes.c_int,
                        ctypes.c_void_p,
                        ctypes.c_void_p]
image_manip.rescaleImage000.argtypes = rescale_fn_arg_types
image_manip.rescaleImage001.argtypes = rescale_fn_arg_types
image_manip.rescaleImage010.argtypes = rescale_fn_arg_types


## rescaleImage
#
# This converts a uint16 image into a uint8 image based on the display
# range. As a side effect it also returns the minimum and maximum values
# in the image.
#
# @param image The original image as numpy.uint16 array.
# @param flip_h Flip horizontal.
# @param flip_v Flip vertical.
# @param transpose Transpose image.
# @param display_range [image value that equals 0, image value that equals 255].
#
# @return [numpy.uint8 image, original image minimum, original image maximum, transposed dimensions]
#
def rescaleImage(image, flip_h, flip_v, transpose, display_range):

    # Create a string specifying the operations that will be performed on the image.
    op_code = ""
    for op in [flip_h, flip_v, transpose]:
        if op:
            op_code += "1"
        else:
            op_code += "0"

    print "op:", op_code

    # Any of these operations will change the final dimensions of the image.
    if (op_code in ["001", "011", "101", "111"]):
        transposed_dimensions = True
        c_rescale = numpy.empty((image.shape[1], image.shape[0]), dtype = numpy.uint8)
    else:
        transposed_dimensions = False        
        c_rescale = numpy.empty((image.shape[0], image.shape[1]), dtype = numpy.uint8)

    image_min = ctypes.c_int(0)
    image_max = ctypes.c_int(0)

    # Get the appropriate C function based on the op_code.
    image_fn = image_manip.__dict__["rescaleImage" + op_code]

    image_fn(c_rescale,
             image,
             image.shape[0],
             image.shape[1],
             display_range[0],
             display_range[1],
             ctypes.byref(image_min),
             ctypes.byref(image_max))

    return [c_rescale, image_min.value, image_max.value, transposed_dimensions]

# Testing
if (__name__ == "__main__"):

    from PIL import Image

    im = Image.open("raw_image.png")
    nim = numpy.ascontiguousarray(numpy.amax(numpy.array(im), 2).astype(numpy.uint16))

    [rs_nim, image_min, image_max, transposed_dimensions] = rescaleImage(nim, False, True, False, [0, 255])
    fim = Image.fromarray(rs_nim)
    fim.save("out.png")

#
# The MIT License
#
# Copyright (c) 2015 Zhuang Lab, Harvard University
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

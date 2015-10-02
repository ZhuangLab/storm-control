#!/usr/bin/python
#
## @file
#
# Python interface to the C image manipulation library. The library
# is used to speed up the rendering of the image in the UI. My experience
# was that for large images, such as those from a sCMOS camera, using numpy
# to do the image scaling and type conversion was not fast enough.
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

try:
    if (sys.platform == "win32"):
        image_manip = ctypes.cdll.LoadLibrary(directory + "c_image_manipulation.dll")
    else:
        image_manip = ctypes.cdll.LoadLibrary(directory + "c_image_manipulation.so")
            
    # C interface definition.
    image_manip.compare.argtypes = [ndpointer(dtype=numpy.uint8),
                                    ndpointer(dtype=numpy.uint8),
                                    ctypes.c_int]
    image_manip.compare.restype = ctypes.c_int
                                                               
    rescale_fn_arg_types = [ndpointer(dtype=numpy.uint8),
                            ndpointer(dtype=numpy.uint16),
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_int,
                            ctypes.c_double,
                            ctypes.c_void_p,
                            ctypes.c_void_p]
    image_manip.rescaleImage000.argtypes = rescale_fn_arg_types
    image_manip.rescaleImage001.argtypes = rescale_fn_arg_types
    image_manip.rescaleImage010.argtypes = rescale_fn_arg_types
    image_manip.rescaleImage011.argtypes = rescale_fn_arg_types
    image_manip.rescaleImage100.argtypes = rescale_fn_arg_types
    image_manip.rescaleImage101.argtypes = rescale_fn_arg_types
    image_manip.rescaleImage110.argtypes = rescale_fn_arg_types
    image_manip.rescaleImage111.argtypes = rescale_fn_arg_types

except OSError:
    print "C image manipulation library not found, reverting to numpy."
    image_manip = None

## compare
#
# This does a bytewise comparison of two images.
#
# @param image1 The first image.
# @param image2 The second image.
#
# @return The number of differences greater than 1.
#
def compare(image1, image2):
    
    if (image1.size != image2.size):
        print "Images are not the same size!"
        return

    return image_manip.compare(image1, image2, image1.size)


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
# @param saturated_value The value above which the image has saturated the camera.
# @param use_numpy (optional) Use numpy even if the C library exists, defaults to False.
#
# @return [numpy.uint8 image, original image minimum, original image maximum]
#
def rescaleImage(image, flip_h, flip_v, transpose, display_range, saturated_value, use_numpy = False):

    # Create a string specifying the operations that will be performed on the image.
    op_code = ""
    for op in [flip_h, flip_v, transpose]:
        if op:
            op_code += "1"
        else:
            op_code += "0"

    # Determine maximum in the rescaled image.
    if saturated_value is not None:
        max_range = 254.0
    else:
        saturated_value = 65536
        max_range = 255.0
        
    # Use C library for image manipulation, this will be faster and less memory intensive.
    if (image_manip is not None) and (not use_numpy):

        if transpose:
            rescaled = numpy.empty((image.shape[1], image.shape[0]), dtype = numpy.uint8)
        else:
            rescaled = numpy.empty((image.shape[0], image.shape[1]), dtype = numpy.uint8)

        image_min = ctypes.c_int(0)
        image_max = ctypes.c_int(0)

        # Get the appropriate C function based on the op_code.
        image_fn = getattr(image_manip, "rescaleImage" + op_code)

        image_fn(rescaled,
                 image,
                 image.shape[0],
                 image.shape[1],
                 display_range[0],
                 display_range[1],
                 saturated_value,
                 max_range,
                 ctypes.byref(image_min),
                 ctypes.byref(image_max))

        image_min = image_min.value
        image_max = image_max.value

    # Fall back to using numpy.
    else:
        image_min = numpy.min(image)
        image_max = numpy.max(image)
            
        if flip_h:
            image = numpy.fliplr(image)
            
        if flip_v:
            image = numpy.flipud(image)

        if transpose:
            image = numpy.transpose(image)
        
        rescaled = image.astype(numpy.float64)
        rescaled = max_range*(rescaled - display_range[0])/(display_range[1] - display_range[0])
        rescaled[(rescaled > max_range)] = max_range 
        rescaled[(rescaled < 0.0)] = 0.0
        
        # Check for saturated pixels
        if saturated_value is not None:
            rescaled[(image >= saturated_value)] = 255.0

        # Convert to contiguous uint8 array.
        rescaled += 0.5
        rescaled = rescaled.astype(numpy.uint8, order='C')

    return [rescaled, image_min, image_max]


# Testing
#
# This does a quick test for all the different possibilities. You will need to provide a raw image.
#
if (__name__ == "__main__"):

    from PIL import Image

    if (len(sys.argv)!=2):
        print "Usage <image_file>"
        exit()
        
    im = Image.open(sys.argv[1])
    nim = numpy.ascontiguousarray(numpy.amax(numpy.array(im), 2).astype(numpy.uint16))

    all_ori = [[False, False, False],
               [False, False, True],
               [False, True, False],
               [False, True, True],
               [True, False, False],
               [True, False, True],
               [True, True, False],
               [True, True, True]]

    #all_ori = [[False, False, False]]
    
    for ori in all_ori:
        print "Testing:", ori
        [flip_h, flip_v, transpose] = ori

        if False:
            [c_nim, image_min, image_max] = rescaleImage(nim, flip_h, flip_v, transpose, [0, 100], None)
            [py_nim, image_min, image_max] = rescaleImage(nim, flip_h, flip_v, transpose, [0, 100], None, True)
        else:
            [c_nim, image_min, image_max] = rescaleImage(nim, flip_h, flip_v, transpose, [0, 100], 101)
            [py_nim, image_min, image_max] = rescaleImage(nim, flip_h, flip_v, transpose, [0, 100], 101, True)

        print "  byte wise comparison:", compare(c_nim, py_nim), "pixels are different."
        
        c_nim = c_nim.astype(numpy.int)
        py_nim = py_nim.astype(numpy.int)

        # Allow single value differences which occur due to differences in rounding.
        mask = (numpy.abs(c_nim - py_nim) > 1)
        
        if (numpy.count_nonzero(mask) > 0):
            print "  Failed", numpy.count_nonzero(mask), numpy.max(numpy.abs(c_nim - py_nim))
            
            fim = Image.fromarray(c_nim.astype(numpy.uint8))
            fim.save("out.png")

            diff = c_nim - py_nim + 128
            fim = Image.fromarray(diff.astype(numpy.uint8))
            fim.save("diff.png")
        else:
            print "  Ok"

            
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

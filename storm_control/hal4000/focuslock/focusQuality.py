#!/usr/bin/python
#
## @file
#
# Python interface to the focus_quality library.
#
# Hazen 10/13
#

from ctypes import *
import numpy
from numpy.ctypeslib import ndpointer
import os
import sys

focus_quality = False

## loadFocusQuality
#
# Loads the focus quality DLL, if it has not already been loaded.
#
def loadFocusQualityDLL():
    global focus_quality
    if not focus_quality:

        directory = os.path.dirname(__file__)
        if (directory == ""):
            directory = "./"
        else:
            directory += "/"

        if (sys.platform == "win32"):
            focus_quality = cdll.LoadLibrary(directory + "focus_quality.dll")
        else:
            focus_quality = cdll.LoadLibrary(directory + "focus_quality.so")

loadFocusQualityDLL()
c_imageGradient = focus_quality.imageGradient
c_imageGradient.argtypes = [ndpointer(dtype=numpy.uint16),
                            c_int,
                            c_int]
c_imageGradient.restype = c_float

## imageGradient
#
# Returns the magnitude of the image gradient in the x direction.
#
def imageGradient(frame):
    return c_imageGradient(frame.getData(),
                           frame.image_x,
                           frame.image_y)


#
# Testing
# 

if __name__ == "__main__":

    import camera.frame as frame
    import numpy
    import time

    image_x = 512
    image_y = 512
    aframe = frame.Frame(numpy.ones((image_x, image_y), dtype = numpy.uint16),
                         0,
                         image_x,
                         image_y,
                         "camera1",
                         True)

    repeats = 200
    start = time.time()
    for i in range(repeats):
        imageGradient(aframe)
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


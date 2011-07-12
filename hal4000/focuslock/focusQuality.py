#!/usr/bin/python
#
# Python interface to the focus_quality library.
#
# Hazen 08/10
#

from ctypes import *
import os

focus_quality = False

def loadFocusQualityDLL():
    global focus_quality
    if not focus_quality:
        if os.path.exists("focus_quality.dll"):
            focus_quality = cdll.LoadLibrary("focus_quality")
        else:
            focus_quality = cdll.LoadLibrary("focuslock/focus_quality")

loadFocusQualityDLL()
c_imageGradient = focus_quality.imageGradient
c_imageGradient.restype = c_float

#
# Returns the magnitude of the image gradient in the x direction.
#

def imageGradient(image, image_x, image_y):
    return c_imageGradient(image,
                           c_int(image_x),
                           c_int(image_y))


#
# Testing
# 

if __name__ == "__main__":
    import time

    image_x = 512
    image_y = 512
    image_type = c_short * (image_x * image_y)
    image = image_type()

    repeats = 200
    start = time.time()
    for i in range(repeats):
        imageGradient(image, image_x, image_y)
    end = time.time()
    print "Time to process an image: ", ((end - start)/repeats), " seconds"


#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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


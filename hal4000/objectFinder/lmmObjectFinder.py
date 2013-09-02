#!/usr/bin/python
#
# Python interface to the LMMoment object finder.
#
# Hazen 09/13
#

from ctypes import *
import os
import sys

lmmoment = False

max_locs = 1000
loc_type = c_float * max_locs


def cleanup():
    lmmoment.cleanup()

def initialize():
    global lmmoment

    directory = os.path.dirname(__file__)
    if not (directory == ""):
        directory += "/"

    lmmoment = cdll.LoadLibrary(directory + "LMMoment.dll")
    lmmoment.initialize()

def findObjects(image, image_x, image_y, threshold):
        x = loc_type()
        y = loc_type()
        n = c_int(max_locs)
        lmmoment.numberAndLocObjects(image,
                                     c_int(image_x),
                                     c_int(image_y),
                                     c_int(threshold),
                                     x,
                                     y,
                                     byref(n))
        return [x, y, n.value]


# testing
if __name__ == "__main__":
    import time

    initialize()

    image_x = 512
    image_y = 512
    image_type = c_short * (image_x * image_y)
    image = image_type()

    repeats = 100
    start = time.time()
    for i in range(repeats):
        [x, y, n] = findObjects(image, image_x, image_y, 100)
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

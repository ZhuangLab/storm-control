#!/usr/bin/python
#
# A fast spot counter based on subtracting the median value
# in each cell, thresholding the image, and then computing
# the center of mass of all the points above the threshold.
#
# Hazen 10/09
#

from ctypes import *
import os
import sys

MEDDLL = 0
def loadDLLs():
    global MEDDLL
    if not(MEDDLL):
        if os.path.exists("MedianCounter.dll"):
            MEDDLL = cdll.LoadLibrary("MedianCounter")
        else:
            MEDDLL = cdll.LoadLibrary("objectFinder/MedianCounter")


class MedFastObjectFinder:
    def __init__(self, cell_size, threshold):
        loadDLLs()
        self.cell_size = cell_size
        self.threshold = threshold
        self.coefficients = [0.0, 1.0]
        self.max_locs = 1000
        self.loc_type = c_float * self.max_locs

    def _checkSize(self, image_x, image_y):
#        if ((image_x % self.cell_size) == 0) and (image_x == image_y):
        if ((image_x % self.cell_size) == 0):
            return 1
        else:
            return 0

    def countObjects(self, image, image_x, image_y):
        if not self._checkSize(image_x, image_y):
            return 0
        counts = float(MEDDLL.number_objects(image,
                                             c_int(image_x),
                                             c_int(image_y),
                                             c_int(self.cell_size),
                                             c_float(self.threshold)))
        number = 0.0
        product = 1.0
        for coeff in self.coefficients:
            number += coeff * product
            product = product * counts
        return number

    def findObjects(self, image, image_x, image_y):
        if not self._checkSize(image_x, image_y):
            return [0, 0, 0]
        x = self.loc_type()
        y = self.loc_type()
        n = c_int(self.max_locs)
        MEDDLL.number_and_loc_objects(image,
                                      c_int(image_x),
                                      c_int(image_y),
                                      c_int(self.cell_size),
                                      c_float(self.threshold),
                                      x,
                                      y,
                                      byref(n))
        return [x, y, n.value]

    def setCellSize(self, cell_size):
        self.cell_size = cell_size

    def setThreshold(self, threshold):
        self.threshold = threshold
        

# testing
if __name__ == "__main__":
    import time

    image_x = 512
    image_y = 512
    image_type = c_short * (image_x * image_y)
    image = image_type()

    mObjF = MedFastObjectFinder(32, 3.0)
        
    repeats = 100
    start = time.time()
    for i in range(repeats):
        print mObjF.countObjects(image, image_x, image_y)
    end = time.time()
    print "Time to process an image: ", ((end - start)/repeats), " seconds"


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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

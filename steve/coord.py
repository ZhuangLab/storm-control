#!/usr/bin/python
#
## @file
#
# Handles coordinate manipulations, mostly converting back
# and forth between pixels and microns.
#
# Hazen 02/13
#

import sc_library.hdebug as hdebug

## Point
#
# There is a lot of conversion back and forth between real positions
# (in microns) and display positions (in pixels). This class is
# designed to make that easier.
#
class Point(object):

    pixels_to_um = 1.0

    ## __init__
    #
    # @param xval The x location of the point.
    # @param yval The y location of the point.
    # @param valtype One of "um" or "pix".
    #
    def __init__(self, xval, yval, valtype):
        if (valtype == "um"):
            self.x_um = xval
            self.y_um = yval
            self.x_pix = xval / self.pixels_to_um
            self.y_pix = yval / self.pixels_to_um
        elif (valtype == "pix"):
            self.x_pix = xval
            self.y_pix = yval
            self.x_um = xval * self.pixels_to_um
            self.y_um = yval * self.pixels_to_um
        else:
            print "(Point) Unknown type:", valtype

    ## __repr__
    #
    def __repr__(self):
        return hdebug.objectToString(self, "coord.Point", ["x_um", "y_um"])
    
    ## getPix
    #
    # @return [x location in pixels, y location in pixels].
    #
    def getPix(self):
        return [self.x_pix, self.y_pix]

    ## getUm
    #
    # @return [x location in microns, y location in microns].
    #
    def getUm(self):
        return [self.x_um, self.y_um]

## umToPix
#
# Converts microns to pixels.
#
# @param um A value in microns.
#
# @return The value of um in pixels.
#
def umToPix(um):
    return um/Point.pixels_to_um

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

#!/usr/bin/env python
"""
Handles coordinate manipulations, mostly converting back
and forth between pixels and microns.

Hazen 02/13
"""

class Point(object):
    """
    There is a lot of conversion back and forth between real positions
    (in microns) and display positions (in pixels). This class is
    designed to make that easier.
    """
    
    # Multiplying by this value will convert pixels to microns.
    pixels_to_um = 1.0
    
    def __init__(self, xval, yval, valtype):
        if (valtype == "um"):
            self.x_um = xval
            self.y_um = yval
            self.x_pix = xval / Point.pixels_to_um
            self.y_pix = yval / Point.pixels_to_um
        elif (valtype == "pix"):
            self.x_pix = xval
            self.y_pix = yval
            self.x_um = xval * Point.pixels_to_um
            self.y_um = yval * Point.pixels_to_um
        else:
            print("(Point) Unknown type:", valtype)

    def __repr__(self):
        return "coord.Point {0:.1f} {1:.1f}".format(self.x_um, self.y_um)
    
    def getPix(self):
        return [self.x_pix, self.y_pix]

    def getUm(self):
        return [self.x_um, self.y_um]

def umToPix(um):
    """
    Converts microns to pixels.
    """
    return um/Point.pixels_to_um

#
# The MIT License
#
# Copyright (c) 2018 Zhuang Lab, Harvard University
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

#!/usr/bin/python
#
## @file
#
# A standalone script for determining the conversion between
# QPD offset and stage z position. Saves the corrected offset
# (in nm) for each frame of the movie.
#
# Hazen 10/14
#

import matplotlib
import matplotlib.pyplot as pyplot
import numpy
import sys

if (len(sys.argv)!=3):
    print "usage: <offset.off file> <results.txt>"
    exit()

import zcal

# Determine stage calibration.
zc = zcal.ZCalibration(None, None, None, None)
zc.stageCalibration(sys.argv[1])
[slope, offset] = zc.getStageFit()

# Plot calibration.
if 0:
    x_vals = numpy.array([-1.5, 1.5])
    y_vals = (x_vals - offset)/slope

    [stage, qpd] = zc.getStageQPD()
    fig = pyplot.figure()
    ax = fig.add_subplot(111)
    ax.scatter(stage, qpd, marker = 'o', s = 2, facecolor = 'red', edgecolor = 'red')
    ax.plot(x_vals, y_vals, color = 'blue')
    pyplot.show()

# Save frame z offsets.
mask = zc.mask
offsets = zc.offsets[:,0]
offsets = 1000.0*(offsets*slope + offset)

numpy.savetxt(sys.argv[2], numpy.c_[mask, offsets], fmt = "%d %f")

#with open(sys.argv[2], "w") as fp:
#    for i in range(mask.size):
#        fp.write(str(mask[i]) + " " + str(offsets[i]) + "\n")

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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

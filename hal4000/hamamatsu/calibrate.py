#!/usr/bin/python
#
# For camera calibration.
#
# Hazen 10/13
#

import numpy
import sys

import hamamatsu_camera as hc

if (len(sys.argv) != 3):
    print "usage: <out filename root> <number frames>"
    exit()

hcam = hc.HamamatsuCamera(0)

# Set camera parameters.
cam_offset = 100
cam_x = 2048
cam_y = 2048
hcam.setPropertyValue("defect_correct_mode", "OFF")
hcam.setPropertyValue("exposure_time", 0.04)
hcam.setPropertyValue("subarray_hsize", cam_x)
hcam.setPropertyValue("subarray_vsize", cam_y)
hcam.setPropertyValue("binning", "1x1")
hcam.setPropertyValue("readout_speed", 1)

print "integration time (seconds):", 1.0/hcam.getPropertyValue("internal_frame_rate")[0]

# Create numpy arrays.
mean = numpy.zeros(cam_x * cam_y, dtype = numpy.int64)
var = numpy.zeros(cam_x * cam_y, dtype = numpy.int64)

# Acquire data.
n_frames = int(sys.argv[2])
hcam.startAcquisition()
for i in range(n_frames):

    # Get frames.
    [frames, dims] = hcam.getFrames()
    if ((i%10)==0):
        print i, len(frames)

    aframe = frames[0].getData().astype(numpy.int16) - cam_offset
    mean += aframe
    var += aframe * aframe

hcam.stopAcquisition()

# Compute mean & variance & save results.
mean = mean/float(n_frames)
var = var/float(n_frames) - mean*mean

numpy.save(sys.argv[1] + "_mean", mean)
numpy.save(sys.argv[1] + "_var", var)

print "mean of mean:", numpy.mean(mean)
print "mean of variance:", numpy.mean(var)

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

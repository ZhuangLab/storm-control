#!/usr/bin/python
#
## @file
#
# This script is used for camera calibration. It records the sum of x and 
# the sum of x*x for every pixel in every frame.
#
# Hazen 10/13
#

import numpy
import sys

import hamamatsu_camera as hc

if (len(sys.argv) != 3):
    print "usage: <filename> <number frames>"
    exit()

hcam = hc.HamamatsuCameraMR(0)

# Set camera parameters.
cam_offset = 100
hcam.setPropertyValue("defect_correct_mode", "OFF")
hcam.setPropertyValue("exposure_time", 0.01)
hcam.setPropertyValue("binning", "1x1")
hcam.setPropertyValue("readout_speed", 2)

if 1:
    cam_x = 2048
    cam_y = 2048
    hcam.setPropertyValue("subarray_hsize", cam_x)
    hcam.setPropertyValue("subarray_vsize", cam_y)

if 0:
    cam_x = 1024
    cam_y = 1024
    hcam.setPropertyValue("subarray_hpos", 512)
    hcam.setPropertyValue("subarray_vpos", 512)
    hcam.setPropertyValue("subarray_hsize", cam_x)
    hcam.setPropertyValue("subarray_vsize", cam_y)

print "integration time (seconds):", 1.0/hcam.getPropertyValue("internal_frame_rate")[0]

# Create numpy arrays.
mean = numpy.zeros(cam_x * cam_y, dtype = numpy.int64)
var = numpy.zeros(cam_x * cam_y, dtype = numpy.int64)

# Acquire data.
#break_on_next_loop = False
n_frames = int(sys.argv[2])
hcam.startAcquisition()
count = 0
while (count < n_frames):

    # Get frames.
    [frames, dims] = hcam.getFrames()
    if ((count%10)==0):
        print "Accumulated", count, "frames, current back log is", len(frames), "frames"
    
    if (len(frames) > 0):
        aframe = frames[0].getData().astype(numpy.int32) - cam_offset
        mean += aframe
        var += aframe * aframe
        count += 1

    #if break_on_next_loop:
    #    break

    #if (len(frames) == 0):
    #    break_on_next_loop = True

hcam.stopAcquisition()

# Compute mean & variance & save results.
#mean = mean/float(n_frames)
#var = var/float(n_frames) - mean*mean

numpy.save(sys.argv[1], [numpy.array([n_frames]), mean, var])

mean_mean = numpy.mean(mean)/float(n_frames)
print "mean of mean:", mean_mean
print "mean of variance:", numpy.mean(var)/float(n_frames) - mean_mean*mean_mean

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

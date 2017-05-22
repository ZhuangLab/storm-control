#!/usr/bin/python
#
## @file
#
# This script is used for camera calibration. It records the sum of x and 
# the sum of x*x for every pixel in every frame.
#
# Hazen 12/16
#

import numpy
import sys
import time

import spinnaker

if (len(sys.argv) != 4):
    print("usage: <camera> <filename> <number frames>")
    exit()

# Initialize
spinnaker.loadSpinnakerDLL(r'C:\Program Files\Point Grey Research\Spinnaker\bin64\vs2013\SpinnakerC_v120.dll')
spinnaker.spinSystemGetInstance()

cam = spinnaker.spinGetCamera(int(sys.argv[1]))

#
# Basic camera configuration. The use of Spinview is recommended as an initial step
# to set all the other parameters, for example "mode7", disabling defect correction
# and using the appropriate AOI.
#
cam.getProperty("VideoMode")
cam.setProperty("VideoMode", "Mode0")
        
cam.getProperty("pgrDefectPixelCorrectionEnable")
cam.setProperty("pgrDefectPixelCorrectionEnable", False)

# Verify that we have turned off this 'feature'.
assert not cam.getProperty("pgrDefectPixelCorrectionEnable").spinNodeGetValue()
        
# Change to 12 bit mode.
cam.getProperty("PixelFormat")
cam.setProperty("PixelFormat", "Mono12Packed")     
cam.setProperty("VideoMode", "Mode7")

# Turn off hardware triggering.
cam.getProperty("TriggerMode")
cam.setProperty("TriggerMode", "Off")
            
# We don't want any of these 'features'.
cam.getProperty("AcquisitionFrameRateAuto")
cam.setProperty("AcquisitionFrameRateAuto", "Off")

cam.getProperty("ExposureAuto")
cam.setProperty("ExposureAuto", "Off")

cam.getProperty("GainAuto")
cam.setProperty("GainAuto", "Off")        

cam.getProperty("pgrExposureCompensationAuto")
cam.setProperty("pgrExposureCompensationAuto", "Off")
        
cam.getProperty("BlackLevelClampingEnable")
cam.setProperty("BlackLevelClampingEnable", False)

cam.getProperty("SharpnessEnabled")
cam.setProperty("SharpnessEnabled", False)

cam.getProperty("GammaEnabled")
cam.setProperty("GammaEnabled", False)

cam.getProperty("OnBoardColorProcessEnabled")
cam.setProperty("OnBoardColorProcessEnabled", False)
        
# Configure acquisition.
cam.getProperty("AcquisitionFrameRate")
cam.setProperty("AcquisitionFrameRate", 50.0)

cam.getProperty("ExposureTime")
cam.setProperty("ExposureTime", cam.getProperty("ExposureTime").spinNodeGetMaximum())

print("Serial Number:", cam.getProperty("DeviceSerialNumber").spinNodeGetValue())
print("Exposure time:", cam.getProperty("ExposureTime").spinNodeGetValue())
print("Frame rate:", cam.getProperty("AcquisitionFrameRate").spinNodeGetValue())

cam.getProperty("BlackLevel")
cam.setProperty("BlackLevel", 1.0)

cam.getProperty("Gain")
cam.setProperty("Gain", 10.0)

print("OffsetX:", cam.getProperty("OffsetX").spinNodeGetValue())
print("OffsetY:", cam.getProperty("OffsetY").spinNodeGetValue())

cam_x = cam.getProperty("Width").spinNodeGetValue()
cam_y = cam.getProperty("Height").spinNodeGetValue()

print("Width:", cam_x)
print("Height:", cam_y)

# Create numpy arrays.
mean = numpy.zeros((cam_x, cam_y), dtype = numpy.int64)
var = numpy.zeros((cam_x, cam_y), dtype = numpy.int64)

# Acquire data.
#break_on_next_loop = False
n_frames = int(sys.argv[3])
cam.startAcquisition()
time.sleep(0.1)
processed = 0
last_processed = -1
captured = 0
start_time = time.time()
while (processed < n_frames):

    # Get frames.
    [frames, dims] = cam.getFrames()
    captured += len(frames)
    
    if ((processed%10)==0) and (processed != last_processed):
        print("Accumulated", processed, "frames, current back log is", len(frames), "frames")
        last_processed = processed
    
    if (len(frames) > 0):
        aframe = frames[0].getData().astype(numpy.int32)
        aframe = numpy.reshape(aframe, (cam_x, cam_y))
        mean += aframe
        var += aframe * aframe
        processed += 1

    #if break_on_next_loop:
    #    break

    #if (len(frames) == 0):
    #    break_on_next_loop = True

end_time = time.time()
cam.stopAcquisition()
cam.release()
spinnaker.spinSystemReleaseInstance()

print("Captured:", captured, "frames in", (end_time - start_time), "seconds.")
print("FPS:", captured/(end_time - start_time))

numpy.save(sys.argv[2], [numpy.array([n_frames]), mean, var])

mean_mean = numpy.mean(mean)/float(n_frames)
print("mean of mean:", mean_mean)
print("mean of variance:", numpy.mean(var)/float(n_frames) - mean_mean*mean_mean)

#
# The MIT License
#
# Copyright (c) 2016 Zhuang Lab, Harvard University
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

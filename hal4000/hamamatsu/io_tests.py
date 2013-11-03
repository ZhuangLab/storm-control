#!/usr/bin/python
#
## @file
#
# For testing how to write 2048 x 2048 pixels at 100fps.
#
# Hazen 10/13
#

import ctypes
import ctypes.util
import numpy
import time

import hamamatsu_camera as hc

print "camera 0 model:", hc.getModelInfo(0)

hcam = hc.HamamatsuCameraMR(0)

# Set camera parameters.
cam_offset = 100
cam_x = 2048
cam_y = 2048
hcam.setPropertyValue("defect_correct_mode", "OFF")
hcam.setPropertyValue("exposure_time", 0.01)
hcam.setPropertyValue("subarray_hsize", cam_x)
hcam.setPropertyValue("subarray_vsize", cam_y)
hcam.setPropertyValue("binning", "1x1")
hcam.setPropertyValue("readout_speed", 2)

# Test image streaming using numpy.
if 1:
    bin_fp = open("e:/zhuang/test.bin", "wb")
    hcam.startAcquisition()
    for i in range(1000):

        # Get frames.
        [frames, dims] = hcam.getFrames()

        # Save frames.
        for aframe in frames:
            np_data = aframe.getData()
            np_data.tofile(bin_fp)

        # Print backlog.
        print i, len(frames)
        if (len(frames) > 20):
            exit()

    hcam.stopAcquisition()
    bin_fp.close()

# Test writing images as separate files w/ numpy.
if 0:
    cur_file = 0
    hcam.startAcquisition()
    for i in range(30):

        # Get frames.
        [frames, dims] = hcam.getFrames()

        # Save frames.
        for aframe in frames:
            np_data = aframe.getData()

            bin_fp = open("e:/zhuang/test" + str(cur_file) + ".bin", "wb")
            np_data.tofile(bin_fp)
            bin_fp.close()
            cur_file += 1

        # Print backlog.
        print i, len(frames)

    hcam.stopAcquisition()

# Test image streaming using numpy.memmap.
if 0:
    fsize = 2048*2048
    max_frame = 1000
    mem_fp = numpy.memmap("e:/zhuang/test.bin", mode = "write", dtype = numpy.uint16, shape = fsize * max_frame)
    hcam.startAcquisition()
    cur_frame = 0
    for i in range(10):
        
        # Get frames.
        [frames, dims] = hcam.getFrames()

        # Save frames.
        for aframe in frames:
            if (cur_frame < max_frame):
                mem_fp[cur_frame*fsize:(cur_frame+1)*fsize] = aframe.getData()
                cur_frame += 1
                
        # Record backlog.
        print i, len(frames)
        
    print "Saved", cur_frame, "frames"
    hcam.stopAcquisition()

# Test image streaming using C / fwrite.
if 0:
    c_lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("c"))
    
    fopen = c_lib.fopen
    fopen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    fopen.restype = ctypes.c_void_p
    
    fwrite = c_lib.fwrite
    fwrite.argtypes = [ctypes.c_void_p,
                       ctypes.c_int,
                       ctypes.c_int,
                       ctypes.c_void_p]
    fwrite.restype = ctypes.c_int

    fclose = c_lib.fclose
    fclose.argtypes = [ctypes.c_void_p]
    fclose.restype = ctypes.c_int

    bin_fp = fopen("e:/zhuang/test.bin", "wb")
    hcam.startAcquisition()
    for i in range(30):
        
        # Get frames.
        [frames, dims] = hcam.getFrames()

        # Save frames.
        for aframe in frames:
            np_data = aframe.getData()
            fwrite(np_data.ctypes.data,
                   2,
                   np_data.size,
                   bin_fp)
            
        # Record backlog.
        print i, len(frames)

    hcam.stopAcquisition()
    fclose(bin_fp)

# Test image streaming using C / write.
if 0:
    c_lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("c"))
    
    _O_WRONLY = int("0x0001", 0)
    _O_CREAT = int("0x0200", 0)

    _S_IWRITE = int("0x0200", 0)

    fopen = c_lib._open
    fopen.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
    fopen.restype = ctypes.c_int
    
    write = c_lib._write
    write.argtypes = [ctypes.c_int,
                      ctypes.c_void_p,
                      ctypes.c_int]
    write.restype = ctypes.c_int

    fclose = c_lib._close
    fclose.argtypes = [ctypes.c_int]

    bin_fd = fopen("e:/zhuang/test.bin", _O_WRONLY + _O_CREAT, _S_IWRITE)
    hcam.startAcquisition()
    for i in range(4):

        # Get frames.
        [frames, dims] = hcam.getFrames()

        # Save frames.
        for aframe in frames:
            np_data = aframe.getData()
            print write(bin_fd, 
                        np_data.ctypes.data, 
                        np_data.size*2)

        # Record backlog.
        print i, len(frames)

    hcam.stopAcquisition()
    fclose(bin_fd)

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

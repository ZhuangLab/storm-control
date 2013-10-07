#!/usr/bin/python
#
# Class for storage of a single frame of camera data
# and its meta-information.
#
# Notes: 
# 1) The which_camera field is expected to be
#    one of the following:
#       "camera1"
#       "camera2"
#
# 2) The numpy data field (np_data) is expected to
#    be of type numpy.uint16.
#
# Hazen 10/13
#

class Frame():

    # FIXME: Are we consistent in the use of master vs. camera1?
    def __init__(self, np_data, frame_number, image_x, image_y, which_camera, master):
        self.image_x = image_x
        self.image_y = image_y
        self.master = master
        self.np_data = np_data
        self.number = frame_number
        self.which_camera = which_camera

    def getData(self):
        return self.np_data

    def getDataPtr(self):
        return self.np_data.ctypes.data

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

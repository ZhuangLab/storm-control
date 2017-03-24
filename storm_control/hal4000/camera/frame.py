#!/usr/bin/env python
"""
Class for storage of a single frame of camera data
or the data from a feed and it's meta-information.

Notes: 
 (1) The numpy data field (np_data) is expected to
     be of type numpy.uint16.
 
Hazen 3/17
"""

class Frame(object):
    """
    Class for the storage of a single frame of camera data
    and it's meta-information.
    """

    def __init__(self, np_data, frame_number, image_x, image_y, which_camera):
        """
        Create a camera frame object.
        FIXME: Are we consistent in the use of master vs. camera1?
        
        np_data - A numpy.uint16 object containing the data for the frame.
        frame_number - The frame number of this frame.
        image_x - The size of the frame in pixels in x.
        image_y - The size of the frame in pixels in y.
        """

        self.image_x = image_x
        self.image_y = image_y
        self.np_data = np_data
        self.frame_number = frame_number
        self.which_camera = which_camera

    def getData(self):
        """
        Returns the numpy object that stores the camera frame data.
        """
        return self.np_data

    def getDataPtr(self):
        """
        Returns a C style pointer to the physical address of the
        camera frame data in the computers memory.
        """
        return self.np_data.ctypes.data


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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

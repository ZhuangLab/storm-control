#!/usr/bin/python
#
# Classes that handles reading STORM movie files. This is used by
# the Steve program and it assumes the existance of an XML file
# that describes everything that one needs to know about a movie.
#
# Hazen 07/15
#

import numpy
import os
from PIL import Image
import re

import sc_library.parameters as parameters

#
# Returns the appropriate object based on the file type as
# saved in the corresponding XML file.
#
def reader(filename):
    filename = os.path.splitext(filename)[0]    
    xml = parameters.Parameters(filename + ".xml")
    file_type = xml.get("film.filetype")
    if (file_type == ".dax"):
        return DaxReader(filename, xml)
    elif (file_type == ".spe"):
        return SpeReader(filename, xml)
    elif (file_type == ".tif"): 
        return TifReader(filename, xml)
    else:
        print file_type, "is not a recognized file type"
        raise IOError("only .dax, .spe and .tif are supported (case sensitive..)")

#
# The superclass containing those functions that 
# are common to reading a STORM movie file.
#
# Subclasses should implement:
#  1. __init__(self, filename, verbose = False)
#     This function should open the file and extract the
#     various key bits of meta-data such as the size in XY
#     and the length of the movie.
#
#  2. loadAFrame(self, frame_number)
#     Load the requested frame and return it as numpy array.
#
class DataReader:

    def __init__(self, filename, xml):
        self.filename = filename
        self.xml = xml

        self.camera = self.xml.get("acquisition.camera")
        
    # Close the file on cleanup.
    def __del__(self):
        if self.fileptr:
            self.fileptr.close()

    # Returns the film name.
    def filmFilename(self):
        return self.filename

    # Returns the film size.
    def filmSize(self):
        return [self.image_width, self.image_height, self.number_frames]

    # Returns the picture x,y,z location.
    def filmLocation(self):
        return [self.xml.get("acquisition.stage_position")]

    # Returns the film focus lock target.
    def lockTarget(self):
        return [self.xml.get("acquisition.lock_target")]

    # Returns the scale used to display the film when
    # the picture was taken.
    def filmScale(self):
        return [[self.xml.get(self.camera + ".scalemin")],
                [self.xml.get(self.camera + ".scalemax")]]


#
# Dax reader class. This is a Zhuang lab custom format.
#
class DaxReader(DataReader):
    
    # dax specific initialization
    def __init__(self, filename, xml):
        DataReader.__init__(self, filename, xml)

        self.bigendian = self.xml.get("film.want_big_endian")
        self.image_height = self.xml.get(self.camera + ".y_pixels")
        self.image_width = self.xml.get(self.camera + ".x_pixels")
        self.number_frames = self.xml.get("acquisition.number_frames")
        
        # open the dax file
        if os.path.exists(filename):
            self.fileptr = open(filename, "rb")
        else:
            self.fileptr = 0
            if verbose:
                print "dax data not found", filename

    # load a frame & return it as a numpy array
    def loadAFrame(self, frame_number):
        if self.fileptr:
            assert frame_number >= 0, "frame_number must be greater than or equal to 0"
            assert frame_number < self.number_frames, "frame number must be less than " + str(self.number_frames)
            self.fileptr.seek(frame_number * self.image_height * self.image_width * 2)
            image_data = numpy.fromfile(self.fileptr, dtype='int16', count = self.image_height * self.image_width)
            image_data = numpy.transpose(numpy.reshape(image_data, [self.image_width, self.image_height]))
            if self.bigendian:
                image_data.byteswap(True)
            return image_data


#
# SPE (Roper Scientific) reader class.
#
class SpeReader(DataReader):

    # Spe specific initialization.
    def __init__(self, filename, xml):
        DataReader.__init__(self, filename, xml)
        
        # Open the file & read the header.
        self.header_size = 4100
        self.fileptr = open(filename, "rb")

        # FIXME: Should check that these match the XML file.        
        self.fileptr.seek(42)
        self.image_width = int(numpy.fromfile(self.fileptr, numpy.uint16, 1)[0])
        self.fileptr.seek(656)
        self.image_height = int(numpy.fromfile(self.fileptr, numpy.uint16, 1)[0])
        self.fileptr.seek(1446)
        self.number_frames = int(numpy.fromfile(self.fileptr, numpy.uint32, 1)[0])

        self.fileptr.seek(108)
        image_mode = int(numpy.fromfile(self.fileptr, numpy.uint16, 1)[0])
        if (image_mode == 0):
            self.image_size = 4 * self.image_width * self.image_height
            self.image_mode = numpy.float32
        elif (image_mode == 1):
            self.image_size = 4 * self.image_width * self.image_height
            self.image_mode = numpy.uint32
        elif (image_mode == 2):
            self.image_size = 2 * self.image_width * self.image_height
            self.image_mode = numpy.int16
        elif (image_mode == 3):
            self.image_size = 2 * self.image_width * self.image_height
            self.image_mode = numpy.uint16
        else:
            print "unrecognized spe image format: ", image_mode

    # load a frame & return it as a numpy array
    def loadAFrame(self, frame_number, cast_to_int16 = True):
        if self.fileptr:
            assert frame_number >= 0, "frame_number must be greater than or equal to 0"
            assert frame_number < self.number_frames, "frame number must be less than " + str(self.number_frames)
            self.fileptr.seek(self.header_size + frame_number * self.image_size)
            image_data = numpy.fromfile(self.fileptr, dtype=self.image_mode, count = self.image_height * self.image_width)
            if cast_to_int16:
                image_data = image_data.astype(numpy.int16)
            image_data = numpy.transpose(numpy.reshape(image_data, [self.image_height, self.image_width]))
            return image_data


#
# TIF reader class.
#
class TifReader(DataReader):
    def __init__(self, filename):
        DataReader.__init__(self, filename, xml)
                
        self.fileptr = False
        self.im = Image.open(filename)
        self.isize = self.im.size

        # FIXME: Should check that these match the XML file.
        self.image_width = self.isize[1]
        self.image_height = self.isize[0]

        self.number_frames = self.xml.get("acquisition.number_frames")

    def loadAFrame(self, frame_number, cast_to_int16 = True):
        assert frame_number >= 0, "frame_number must be greater than or equal to 0"
        assert frame_number < self.number_frames, "frame number must be less than " + str(self.number_frames)
        self.im.seek(frame_number)
        image_data = numpy.array(list(self.im.getdata()))
        assert len(image_data.shape) == 1, "not a monochrome tif image."
        if cast_to_int16:
            image_data = image_data.astype(numpy.int16)
        image_data = numpy.transpose(numpy.reshape(image_data, (self.image_width, self.image_height)))
        return image_data


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

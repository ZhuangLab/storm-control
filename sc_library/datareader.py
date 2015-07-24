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
# Creates a StormXMLObject from a .inf file that can be
# used by Steve. Note that this object is missing many
# of the properties of the standard object created from
# a setting xml file.
#
def infToXmlObject(filename):

    xml = parameters.StormXMLObject([])

    # Mark as "fake".
    xml.set("faked_xml", True)
    
    # Add acquisition sub-object.
    xml.set("acquisition", parameters.StormXMLObject([]))
    xml.set("acquisition.camera", "camera1")
    
    # Add camera1 sub-object.
    xml.set("camera1", parameters.StormXMLObject([]))

    # Add film sub-object.
    xml.set("film", parameters.StormXMLObject([]))
    
    # Add mosaic sub-object.
    xml.set("mosaic", parameters.StormXMLObject([]))

    # Figure out movie type.
    no_ext_name = os.path.splitext(filename)[0]
    if os.path.exists(no_ext_name + ".dax"):
        xml.set("film.filetype", ".dax")
    elif os.path.exists(no_ext_name + ".spe"):
        xml.set("film.filetype", ".spe")
    elif os.path.exists(no_ext_name + ".tif"):
        xml.set("film.filetype", ".tif")
    else:
        raise IOError("only .dax, .spe and .tif are supported (case sensitive..)")        
        
    # Extract the movie information from the associated inf file.
    size_re = re.compile(r'frame dimensions = ([\d]+) x ([\d]+)')
    length_re = re.compile(r'number of frames = ([\d]+)')
    endian_re = re.compile(r' (big|little) endian')
    stagex_re = re.compile(r'Stage X = ([\d\.\-]+)')
    stagey_re = re.compile(r'Stage Y = ([\d\.\-]+)')
    scalemax_re = re.compile(r'scalemax = ([\d\.\-]+)')
    scalemin_re = re.compile(r'scalemin = ([\d\.\-]+)')
    parameters_re = re.compile(r'parameters file = (.+)')

    with open(filename) as fp:
        for line in fp:
            m = size_re.match(line)
            if m:
                xml.set("camera1.y_pixels", int(m.group(1)))
                xml.set("camera1.x_pixels", int(m.group(2)))

            m = length_re.match(line)
            if m:
                xml.set("acquisition.number_frames", int(m.group(1)))
                
            m = endian_re.search(line)
            if m:
                if (m.group(1) == "big"):
                    xml.set("film.want_big_endian", True)
                else:
                    xml.set("film.want_big_endian", False)
                    
            m = stagex_re.match(line)
            if m:
                stage_x = float(m.group(1))
                
            m = stagey_re.match(line)
            if m:
                stage_y = float(m.group(1))
                
            m = scalemax_re.match(line)
            if m:
                xml.set("camera1.scalemax", int(m.group(1)))
                
            m = scalemin_re.match(line)
            if m:
                xml.set("camera1.scalemin", int(m.group(1)))
                
            m = parameters_re.match(line)
            if m:
                xml.set("parameters_file", m.group(1))
                
    xml.set("acquisition.stage_position", [stage_x, stage_y, 0.0])
    return xml

#
# Returns the appropriate object based on the file type as
# saved in the corresponding XML file.
#
def reader(filename):
    no_ext_name = os.path.splitext(filename)[0]

    # Look for XML file.
    if os.path.exists(no_ext_name + ".xml"):
        xml = parameters.parameters(no_ext_name + ".xml", recurse = True)

    # If it does not exist, then create the xml object
    # from the .inf file.
    elif os.path.exists(no_ext_name + ".inf"):
        xml = infToXmlObject(no_ext_name + ".inf")

    else:
        raise IOError("Could not find an associated .xml or .inf file for " + filename)

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
        self.fileptr = False
        self.filename = filename
        self.xml = xml

        self.camera = self.xml.get("acquisition.camera")
        
    # Close the file on cleanup.
    def __del__(self):
        self.closeFilePtr()

    # Check the requested frame number to be sure it is in range.
    def checkFrameNumber(self, frame_number):
        if (frame_number < 0):
            raise IOError("frame_number must be greater than or equal to 0")
        if (frame_number >= self.number_frames):
            raise IOError("frame number must be less than " + str(self.number_frames))
            
    # Close the file.
    def closeFilePtr(self):
        if self.fileptr:
            self.fileptr.close()
            
    # Returns the film name.
    def filmFilename(self):
        return self.filename

    # Returns the film parameters.
    def filmParameters(self):
        return self.xml
        
    # Returns the film size.
    def filmSize(self):
        return [self.image_width, self.image_height, self.number_frames]

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
        self.fileptr = open(filename, "rb")

    # load a frame & return it as a numpy array
    def loadAFrame(self, frame_number):
        if self.fileptr:
            self.checkFrameNumber(frame_number)
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
            self.checkFrameNumber(frame_number)
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
    def __init__(self, filename, xml):
        DataReader.__init__(self, filename, xml)
                
        self.fileptr = False
        self.im = Image.open(filename)
        self.isize = self.im.size

        # FIXME: Should check that these match the XML file.
        self.image_width = self.isize[1]
        self.image_height = self.isize[0]

        self.number_frames = self.xml.get("acquisition.number_frames")

    def loadAFrame(self, frame_number, cast_to_int16 = True):
        self.checkFrameNumber(frame_number)
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

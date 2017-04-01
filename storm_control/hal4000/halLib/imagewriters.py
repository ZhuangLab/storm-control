#!/usr/bin/env python
"""
Image file writers for various formats.

Hazen 03/17
"""

import copy
import datetime
import struct
import tifffile

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

def availableFileFormats():
    """
    Return a list of the available movie formats.
    """
#    return [".dax", ".spe", ".tif"]
    return [".dax", ".tif"]

def createFileWriter(feed_info, film_settings):
    """
    This is convenience function which creates the appropriate file writer
    based on the filetype.
    """
    ft = film_settings["filetype"]
    if (ft == ".dax"):
        return DaxFile(feed_info = feed_info, film_settings = film_settings)
    elif (ft == ".spe"):
        return SPEFile(feed_info = feed_info, film_settings = film_settings)
    elif (ft == ".tif"):
        return TIFFile(feed_info = feed_info, film_settings = film_settings)
    else:
        raise halExceptions.HalException("Unknown output file format '" + ft + "'")


class BaseFileWriter(object):

    def __init__(self, feed_info = None, film_settings = None, **kwds):
        super().__init__(**kwds)
        self.feed_info = feed_info
        self.film_settings = film_settings

        # This is the frame size in MB.
        self.frame_size = self.feed_info.getParameter("bytes_per_frame") *  0.000000953674
        self.number_frames = 0

        # Figure out the filename.
        self.basename = self.film_settings["basename"]
        if (len(self.feed_info.getParameter("extension")) != 0):
            self.basename += "_" + self.feed_info.getParameter("extension")
        self.filename = self.basename + self.film_settings["filetype"]

    def saveFrame(self):
        self.number_frames += 1
        return self.frame_size


class DaxFile(BaseFileWriter):
    """
    Dax file writing class.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.fp = open(self.filename, "wb")

    def closeFile(self):
        """
        Close the file and write a very simple .inf file. All the metadata is
        now stored in the .xml file that is saved with each recording.
        """
        self.fp.close()

        w = str(self.feed_info.getParameter("x_pixels"))
        h = str(self.feed_info.getParameter("y_pixels"))
        with open(self.basename + ".inf", "w") as inf_fp:
            inf_fp.write("binning = 1 x 1\n")
            inf_fp.write("data type = 16 bit integers (binary, little endian)\n")
            inf_fp.write("frame dimensions = " + w + " x " + h + "\n")
            inf_fp.write("number of frames = " + str(self.number_frames) + "\n")
            if True:
                inf_fp.write("x_start = 1\n")
                inf_fp.write("x_end = " + w + "\n")
                inf_fp.write("y_start = 1\n")
                inf_fp.write("y_end = " + h + "\n")
            inf_fp.close()

    def saveFrame(self, frame):
        np_data = frame.getData()
        np_data.tofile(self.fp)
        return super().saveFrame()


class SPEFile(BaseFileWriter):
    """
    SPE file writing class.

    FIXME: This has not been tested, could be broken..
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.fp = open(self.filename, "wb")
        
        header = chr(0) * 4100
        self.fp.write(header)

        # NOSCAN
        self.fp.seek(34)
        self.fp.write(struct.pack("h", -1))

        # FACCOUNT (width)
        self.fp.seek(42)
        self.fp.write(struct.pack("h", self.feed_info.getParameter(x_pixels)))

        # DATATYPE
        self.fp.seek(108)
        self.fp.write(struct.pack("h", 3))
           
        # LNOSCAN
        self.fp.seek(664)
        self.fp.write(struct.pack("h", -1))

        # STRIPE (height)
        self.fp.seek(656)
        self.fp.write(struct.pack("h", self.feed_info.getParameter("y_pixels")))

        self.fp.seek(4100)

    def saveFrame(self, frame):
        np_data = frame.getData()
        np_data.tofile(self.file_ptrs[index])
        return super().saveFrame()

    def closeFile(self):
        self.fp.seek(1446)
        self.fp.write(struct.pack("i", self.number_frames))


class TIFFile(BaseFileWriter):
    """
    TIF file writing class. Note that this is a normal tif file format and 
    not a big tif format so the maximum size is limited to 4GB (more or less).
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.metadata = {'unit' : 'um'}
        self.resolution = (self.film_settings["pixel_size"], self.film_settings["pixel_size"], None)
        self.tif = tifffile.TiffWriter(self.filename)
        
    def saveFrame(self, frame):
        image = frame.getData()
        self.tif.save(image.reshape((frame.image_y, frame.image_x)),
                      metadata = self.metadata,
                      resolution = self.resolution)
        return super().saveFrame()
                      
    def closeFile(self):
        self.tif.close()

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
 

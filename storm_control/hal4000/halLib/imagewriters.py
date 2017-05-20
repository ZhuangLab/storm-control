#!/usr/bin/env python
"""
Image file writers for various formats.

Hazen 03/17
"""

import copy
import datetime
import struct
import tifffile

from PyQt5 import QtCore

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params


class ImageWriterException(halExceptions.HalException):
    pass


def availableFileFormats():
    """
    Return a list of the available movie formats.
    """
    #
    # FIXME: Decouple extension from file type so that big tiffs can
    #        have a normal name, and don't need the '.big' in the
    #        extension.
    #
#    return [".dax", ".spe", ".tif"]
    return [".dax", ".tif", ".big.tif"]

def createFileWriter(camera_functionality, film_settings):
    """
    This is convenience function which creates the appropriate file writer
    based on the filetype.
    """
    ft = film_settings.getFiletype()
    if (ft == ".dax"):
        return DaxFile(camera_functionality = camera_functionality,
                       film_settings = film_settings)
    elif (ft == ".big.tif"):
        return TIFFile(bigtiff = True,
                       camera_functionality = camera_functionality,
                       film_settings = film_settings)
    elif (ft == ".spe"):
        return SPEFile(camera_functionality = camera_functionality,
                       film_settings = film_settings)
    elif (ft == ".tif"):
        return TIFFile(camera_functionality = camera_functionality,
                       film_settings = film_settings)
    else:
        raise ImageWriterException("Unknown output file format '" + ft + "'")


class BaseFileWriter(object):

    def __init__(self, camera_functionality = None, film_settings = None, **kwds):
        super().__init__(**kwds)
        self.cam_fn = camera_functionality
        self.film_settings = film_settings
        self.stopped = False

        # This is the frame size in MB.
        self.frame_size = self.cam_fn.getParameter("bytes_per_frame") *  0.000000953674
        self.number_frames = 0

        # Figure out the filename.
        self.basename = self.film_settings.getBasename()
        if (len(self.cam_fn.getParameter("extension")) != 0):
            self.basename += "_" + self.cam_fn.getParameter("extension")
        self.filename = self.basename + self.film_settings.getFiletype()

        # Connect the camera functionality.
        self.cam_fn.newFrame.connect(self.saveFrame)
        self.cam_fn.stopped.connect(self.handleStopped)

    def closeWriter(self):
        assert self.stopped
        self.cam_fn.newFrame.disconnect(self.saveFrame)
        self.cam_fn.stopped.disconnect(self.handleStopped)

    def getSize(self):
        return self.frame_size * self.number_frames
    
    def handleStopped(self):
        self.stopped = True

    def isStopped(self):
        return self.stopped
        
    def saveFrame(self):
        self.number_frames += 1


class DaxFile(BaseFileWriter):
    """
    Dax file writing class.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.fp = open(self.filename, "wb")

    def closeWriter(self):
        """
        Close the file and write a very simple .inf file. All the metadata is
        now stored in the .xml file that is saved with each recording.
        """
        super().closeWriter()
        self.fp.close()

        w = str(self.cam_fn.getParameter("x_pixels"))
        h = str(self.cam_fn.getParameter("y_pixels"))
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
        super().saveFrame()
        np_data = frame.getData()
        np_data.tofile(self.fp)


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

    def closeWriter(self):
        super().closeWriter()
        self.fp.seek(1446)
        self.fp.write(struct.pack("i", self.number_frames))

    def saveFrame(self, frame):
        super().saveFrame()
        np_data = frame.getData()
        np_data.tofile(self.file_ptrs[index])


class TIFFile(BaseFileWriter):
    """
    TIF file writing class. This supports both normal and 'big' tiff.
    """
    def __init__(self, bigtiff = False, **kwds):
        super().__init__(**kwds)
        self.metadata = {'unit' : 'um'}
        if bigtiff:
            self.resolution = (25400.0/self.film_settings.getPixelSize(),
                               25400.0/self.film_settings.getPixelSize())
            self.tif = tifffile.TiffWriter(self.filename,
                                           bigtiff = bigtiff)
        else:
            self.resolution = (1.0/self.film_settings.getPixelSize(), 1.0/self.film_settings.getPixelSize())
            self.tif = tifffile.TiffWriter(self.filename,
                                           imagej = True)

    def closeWriter(self):
        super().closeWriter()
        self.tif.close()
        
    def saveFrame(self, frame):
        super().saveFrame()
        image = frame.getData()
        self.tif.save(image.reshape((frame.image_y, frame.image_x)),
                      metadata = self.metadata,
                      resolution = self.resolution)


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
 

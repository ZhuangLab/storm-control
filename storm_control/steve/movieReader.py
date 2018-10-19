#!/usr/bin/env python
"""
Classes for reading HAL movies and XML. 

Some of this is a copy of storm_analysis.sa_library.datareader, except 
that support for the spe and fits formats has been removed.

Hazen 10/18
"""

import hashlib
import numpy
import os
import re
import tifffile

import storm_control.sc_library.parameters as parameters


def inferReader(movie_filename, verbose = False):
    """
    Given a file name this will try to return the appropriate
    reader based on the file extension.
    """
    ext = os.path.splitext(movie_filename)[1]
    if (ext == ".dax"):
        return DaxReader(movie_filename, verbose = verbose)
    elif (ext == ".tif") or (ext == ".tiff"):
        return TifReader(movie_filename, verbose = verbose)
    else:
        print(ext, "is not a recognized file type")
        raise IOError("only .dax and .tif are supported (case sensitive..)")


def infToStormXML(inf_filename):
    """
    Creates a StormXMLObject from a .inf file that can be
    used by Steve. Note that this object is missing many
    of the properties of the standard object created from
    a setting xml file.
    """

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
    
    # Add mosaic sub-object with fake objective.
    xml.set("mosaic", parameters.StormXMLObject([]))
    xml.set("mosaic.objective", "fake")

    # Figure out movie type.
    no_ext_name = os.path.splitext(inf_filename)[0]
    if os.path.exists(no_ext_name + ".dax"):
        xml.set("film.filetype", ".dax")
    elif os.path.exists(no_ext_name + ".tif"):
        xml.set("film.filetype", ".tif")
    else:
        raise IOError("only .dax and .tif are supported (case sensitive..)")        
        
    # Extract the movie information from the associated inf file.
    size_re = re.compile(r'frame dimensions = ([\d]+) x ([\d]+)')
    length_re = re.compile(r'number of frames = ([\d]+)')
    endian_re = re.compile(r' (big|little) endian')
    stagex_re = re.compile(r'Stage X = ([\d\.\-]+)')
    stagey_re = re.compile(r'Stage Y = ([\d\.\-]+)')
    scalemax_re = re.compile(r'scalemax = ([\d\.\-]+)')
    scalemin_re = re.compile(r'scalemin = ([\d\.\-]+)')
    parameters_re = re.compile(r'parameters file = (.+)')

    with open(inf_filename) as fp:
        for line in fp:
            m = size_re.match(line)
            if m:
                # y_pixels = height, x_pixels = width.
                xml.set("camera1.y_pixels", int(m.group(2)))
                xml.set("camera1.x_pixels", int(m.group(1)))

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

    pos_string = "{0:.2f},{1:.2f},0.00".format(stage_x, stage_y)
    xml.set("acquisition.stage_position", pos_string)
    return xml


def paramsToStormXML(params_filename):
    """
    Returns a StormXMLObject created from a parameters file.
    """
    return parameters.parameters(params_filename, recurse = True)


class Reader(object):
    """
    The superclass containing those functions that 
    are common to reading a STORM movie file.

    Subclasses should implement:
     1. __init__(self, filename, verbose = False)
        This function should open the file and extract the
        various key bits of meta-data such as the size in XY
        and the length of the movie.

     2. loadAFrame(self, frame_number)
        Load the requested frame and return it as numpy array.
    """
    def __init__(self, filename, verbose = False):
        super(Reader, self).__init__()
        self.filename = filename
        self.fileptr = None
        self.verbose = verbose

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, etype, value, traceback):
        self.close()

    def averageFrames(self, start = False, end = False):
        """
        Average multiple frames in a movie.
        """
        if (not start):
            start = 0
        if (not end):
            end = self.number_frames 

        length = end - start
        average = numpy.zeros((self.image_height, self.image_width), numpy.float)
        for i in range(length):
            if self.verbose and ((i%10)==0):
                print(" processing frame:", i, " of", self.number_frames)
            average += self.loadAFrame(i + start)
            
        average = average/float(length)
        return average

    def close(self):
        if self.fileptr is not None:
            self.fileptr.close()
            self.fileptr = None
        
    def filmFilename(self):
        """
        Returns the film name.
        """
        return self.filename

    def filmSize(self):
        """
        Returns the film size.
        """
        return [self.image_width, self.image_height, self.number_frames]

    def loadAFrame(self, frame_number):
        assert frame_number >= 0, "Frame_number must be greater than or equal to 0, it is " + str(frame_number)
        assert frame_number < self.number_frames, "Frame number must be less than " + str(self.number_frames)


class DaxReader(Reader):
    """
    Dax reader class. This is a Zhuang lab custom format.
    """
    def __init__(self, filename, verbose = False):
        super(DaxReader, self).__init__(filename, verbose = verbose)
        
        # save the filenames
        dirname = os.path.dirname(filename)
        if (len(dirname) > 0):
            dirname = dirname + "/"
        self.inf_filename = dirname + os.path.splitext(os.path.basename(filename))[0] + ".inf"

        # defaults
        self.image_height = None
        self.image_width = None

        # extract the movie information from the associated inf file
        size_re = re.compile(r'frame dimensions = ([\d]+) x ([\d]+)')
        length_re = re.compile(r'number of frames = ([\d]+)')
        endian_re = re.compile(r' (big|little) endian')

        inf_file = open(self.inf_filename, "r")
        while True:
            line = inf_file.readline()
            if not line: break
            m = size_re.match(line)
            if m:
                self.image_height = int(m.group(2))
                self.image_width = int(m.group(1))
            m = length_re.match(line)
            if m:
                self.number_frames = int(m.group(1))
            m = endian_re.search(line)
            if m:
                if m.group(1) == "big":
                    self.bigendian = 1
                else:
                    self.bigendian = 0

        inf_file.close()

        # Error out if we couldn't figure out the image size.
        if not self.image_height:
            raise IOError("Could not determine image size!")

        # Open the dax file
        if os.path.exists(filename):
            self.fileptr = open(filename, "rb")
        else:
            if self.verbose:
                print("dax data not found", filename)

    def loadAFrame(self, frame_number):
        """
        Load a frame & return it as a numpy array.
        """
        super(DaxReader, self).loadAFrame(frame_number)

        self.fileptr.seek(frame_number * self.image_height * self.image_width * 2)
        image_data = numpy.fromfile(self.fileptr, dtype='uint16', count = self.image_height * self.image_width)
        image_data = numpy.reshape(image_data, [self.image_height, self.image_width])
        if self.bigendian:
            image_data.byteswap(True)
        return image_data


class TifReader(Reader):
    """
    TIF reader class.
    
    When given tiff files with multiple pages and multiple frames per
    page this is just going to read the file as if it was one long movie.
    """
    def __init__(self, filename, verbose = False):
        super(TifReader, self).__init__(filename, verbose)

        # Save the filename
        self.fileptr = tifffile.TiffFile(filename)
        number_pages = len(self.fileptr.pages)

        # Get shape by loading first frame
        self.isize = self.fileptr.asarray(key=0).shape

        # Check if each page has multiple frames.
        if (len(self.isize) == 3):
            self.frames_per_page = self.isize[0]
            self.image_height = self.isize[1]
            self.image_width = self.isize[2]
            
        else:
            self.frames_per_page = 1
            self.image_height = self.isize[0]
            self.image_width = self.isize[1]

        if self.verbose:
            print("{0:0d} frames per page, {1:0d} pages".format(self.frames_per_page, number_pages))
        
        self.number_frames = self.frames_per_page * number_pages
        self.page_number = -1
        self.page_data = None

    def loadAFrame(self, frame_number, cast_to_int16 = True):
        super(TifReader, self).loadAFrame(frame_number)

        # Load the right frame from the right page.
        if (self.frames_per_page > 1):
            page = int(frame_number/self.frames_per_page)
            frame = frame_number % self.frames_per_page

            # This is an optimization for files with a large number of frames
            # per page. In this case tifffile will keep loading the entire
            # page over and over again, which really slows everything down.
            # Ideally tifffile would let us specify which frame on the page
            # we wanted.
            #
            # Since it was going to load the whole thing anyway we'll have
            # memory overflow either way, so not much we can do about that
            # except hope for small file sizes.
            #
            if (page != self.page_number):
                self.page_data = self.fileptr.asarray(key = page)
                self.page_number = page
            image_data = self.page_data[frame,:,:]
        else:
            image_data = self.fileptr.asarray(key = frame_number)            
            assert (len(image_data.shape) == 2), "not a monochrome tif image."
                
        if cast_to_int16:
            image_data = image_data.astype(numpy.uint16)
                
        return image_data

    
#
# The MIT License
#
# Copyright (c) 2018 Zhuang Lab, Harvard University
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

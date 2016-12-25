#!/usr/bin/python
#
## @file
#
# Writing 16 bit multi-frame tiff files. The entire image 
# is written as a single strip to make things a bit less 
# of headache.
#
# Hazen 10/13
#

import struct
import time

# some tag definitions to make the code easier to read
NewSubfileType = 254
ImageWidth = 256
ImageLength = 257
BitsPerSample = 258
Compression = 259
PhotometricInterpretation = 262
ImageDescription = 270
StripOffsets = 273
SamplesPerPixel = 277
RowsPerStrip = 278
StripByteCounts = 279
XResolution = 282
YResolution = 283
ResolutionUnit = 296
Software = 305
DateTime = 306

## TiffWriter
#
# This class encapsulates writing 16 bit single channel tif movies to a file.
#
class TiffWriter:

    ## __init__
    #
    # @param filename The name of the tif file to write.
    # @param bytes_per_pixel (Optional) This is 2 bytes (16 bits) by default.
    # @param software (Optional) The name of the program that is "creating" the tif file, defaults to "unknown".
    # @param x_pizel_size (optional) The size of a pixel in x in microns.
    # @param y_pizel_size (optional) The size of a pixel in y in microns.
    #
    def __init__(self, filename, bytes_per_pixel = 2, software = "unknown", x_pixel_size = 1.0, y_pixel_size = 1.0):
        self.bytes_per_pixel = 2
        self.fp = open(filename, "wb")
        self.frames = 0
        self.last_ifd_offset = 0
        self.newsubfiletag_loc = 0
        self.software = software + chr(0)
        self.x_pixel_size = x_pixel_size
        self.y_pixel_size = y_pixel_size

        # Get the current time, in the correct format.
        cur_time = time.localtime()
        self.date_time = "{0:04d}:{1:02d}:{2:02d} {3:02d}:{4:02d}:{5:02d}".format(cur_time.tm_year,
                                                                                  cur_time.tm_mon,
                                                                                  cur_time.tm_mday,
                                                                                  cur_time.tm_hour,
                                                                                  cur_time.tm_min,
                                                                                  cur_time.tm_sec) + chr(0)
        # Construct ImageJ format description.
        self.imagej_desc = "ImageJ=1.49i\nunit=um\n"

        #
        # Write tiff header.
        #
        self.fp.write(struct.pack("2s", "II"))
        self.fp.write(struct.pack("H", 42))
        self.fp.write(struct.pack("I", self.fp.tell()+4))

    ## addFrame
    #
    # Adds a frame (numpy.uint16 array) to the tiff image.
    #
    # @param np_frame The image data as a numpy.uint16 array.
    # @param x_size The size of the frame in x (in pixels).
    # @param y_size The size of the frame in y (in pixels).
    #
    def addFrame(self, np_frame, x_size, y_size):
        cur_loc = self.fp.tell()
        num_tags = 16

        # Update previous ifd
        if (self.last_ifd_offset != 0):
            self.fp.seek(self.last_ifd_offset)
            self.fp.write(struct.pack("I", cur_loc))
            self.fp.seek(cur_loc)

        # Calculations
        image_size = x_size * y_size * self.bytes_per_pixel
        ifd_end = cur_loc + 2 + num_tags*12 + 4
        software_offset = ifd_end + 2*8
        datetime_offset = software_offset + len(self.software)
        imagej_offset = datetime_offset + len(self.date_time)
        image_offset =  imagej_offset + len(self.imagej_desc)

        # number of tags
        self.fp.write(struct.pack("H", num_tags))

        if (self.frames == 0):
            self.newsubfiletag_loc = self.fp.tell()
            self.writeTag(NewSubfileType, "long", 1, 0)
        else:
            self.writeTag(NewSubfileType, "long", 1, 2)
        self.writeTag(ImageWidth, "long", 1, x_size)
        self.writeTag(ImageLength, "long", 1, y_size)
        self.writeTag(BitsPerSample, "short", 1, 8 * self.bytes_per_pixel)
        self.writeTag(Compression, "short", 1, 1)
        self.writeTag(PhotometricInterpretation, "short", 1, 1)
        self.writeTag(ImageDescription, "ascii", len(self.imagej_desc), imagej_offset)
        self.writeTag(StripOffsets, "long", 1, image_offset)
        self.writeTag(SamplesPerPixel, "short", 1, 1)
        self.writeTag(RowsPerStrip, "long", 1, y_size)
        self.writeTag(StripByteCounts, "long", 1, image_size)
        self.writeTag(XResolution, "rational", 1, ifd_end)
        self.writeTag(YResolution, "rational", 1, ifd_end + 8)
        self.writeTag(ResolutionUnit, "short", 1, 1)
        self.writeTag(Software, "ascii", len(self.software), software_offset)
        self.writeTag(DateTime, "ascii", len(self.date_time), datetime_offset)

        # Next IFD offset (4 bytes)
        self.last_ifd_offset = self.fp.tell()
        self.fp.write(struct.pack("I", 0))

        # X resolution (8 bytes)
        denom = 1000000.0
        numer = self.x_pixel_size * denom
        self.fp.write(struct.pack("I", int(denom)))
        self.fp.write(struct.pack("I", int(numer)))

        # Y resolution (8 bytes)
        numer = self.y_pixel_size * denom
        self.fp.write(struct.pack("I", int(denom)))
        self.fp.write(struct.pack("I", int(numer)))

        # Software (arb)
        self.fp.write(struct.pack(str(len(self.software)) + "s", self.software))

        # DateTime (arb)
        self.fp.write(struct.pack(str(len(self.date_time)) + "s", self.date_time))

        # ImageDescription (arb)
        self.fp.write(struct.pack(str(len(self.imagej_desc)) + "s", self.imagej_desc))
        
        # Write the frame.
        np_frame.tofile(self.fp)
        self.frames += 1

    ## close
    #
    # Cleans up & closes the file.
    #
    def close(self):
        if (self.frames > 1):
            self.fp.seek(self.newsubfiletag_loc)
            self.writeTag(NewSubfileType, "long", 1, 2)
        self.fp.close()

    ## writeTag
    #
    # Write a single tiff tag at current fp location.
    #
    # @param tag A tif tag (this is a integer, see tag definitions at the start of the file.
    # @param tag_type The tag type, 2 = ascii, 3 = short, 4 = long, 5 = rational.
    # @param count The number of elements in tag (this is usually 1, except for ascii where it is the length of the string).
    # @param value The tag value.
    #
    def writeTag(self, tag, tag_type, count, value):
        self.fp.write(struct.pack("H", tag))        # tag

        # type (2 = ascii, 3 = short, 4 = long, 5 = rational)
        if (tag_type == "ascii"):
            self.fp.write(struct.pack("H", 2))
            self.fp.write(struct.pack("I", count))
            self.fp.write(struct.pack("I", value))
        elif (tag_type == "short"):
            self.fp.write(struct.pack("H", 3))
            self.fp.write(struct.pack("I", count))  
            self.fp.write(struct.pack("H", value))
            self.fp.write(struct.pack("H", 0))
        elif (tag_type == "long"):
            self.fp.write(struct.pack("H", 4))
            self.fp.write(struct.pack("I", count))  
            self.fp.write(struct.pack("I", value))
        elif (tag_type == "rational"):
            self.fp.write(struct.pack("H", 5))
            self.fp.write(struct.pack("I", count))  
            self.fp.write(struct.pack("I", value))
        else:
            print "unknown tag_type", tag_type, "this tiff file will be mal-formed"

    
if __name__ == "__main__":

    import numpy
    import sys

    im = TiffWriter(sys.argv[1], x_pixel_size = 0.160)

    frame_x = 200
    frame_y = 200
    frame = 10 * numpy.ones((frame_x, frame_y), dtype = numpy.uint16)

    for i in range(5):
        #frame = frame * (i + 2)
        im.addFrame(frame, frame_x, frame_y)

    im.close()


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
 

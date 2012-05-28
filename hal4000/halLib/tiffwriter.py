#!/usr/bin/python
#
# Writing 16 bit multi-frame tiff files. The entire image 
# is written as a single strip to make things a bit less 
# of headache.
#
# Hazen 5/12
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
StripOffsets = 273
SamplesPerPixel = 277
RowsPerStrip = 278
StripByteCounts = 279
XResolution = 282
YResolution = 283
ResolutionUnit = 296
Software = 305
DateTime = 306

class TiffWriter:
    def __init__(self, filename, bytes_per_pixel = 2, software = "unknown"):
        self.bytes_per_pixel = 2
        self.date_time = "2012:05:28 11:45:22" + chr(0)
        self.fp = open(sys.argv[1], "wb")
        self.frames = 0
        self.last_ifd_offset = 0
        self.newsubfiletag_loc = 0
        self.software = software + chr(0)

        #
        # write tiff header
        #
        self.fp.write(struct.pack("2s", "II"))
        self.fp.write(struct.pack("H", 42))
        self.fp.write(struct.pack("I", self.fp.tell()+4))

    # Adds a frame to the tiff image
    def addFrame(self, frame, x_size, y_size):
        cur_loc = self.fp.tell()
        num_tags = 15

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
        image_offset =  datetime_offset + len(self.date_time)

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
        self.fp.write(struct.pack("I", 1))
        self.fp.write(struct.pack("I", 1))

        # Y resolution (8 bytes)
        self.fp.write(struct.pack("I", 1))
        self.fp.write(struct.pack("I", 1))

        # Software (arb)
        self.fp.write(struct.pack(str(len(self.software)) + "s", self.software))

        # DateTime (arb)
        self.fp.write(struct.pack(str(len(self.date_time)) + "s", self.date_time))

        # Write the frame.
        self.fp.write(frame)
        self.frames += 1

    # Cleans up & closes the file
    def close(self):
        if (self.frames > 1):
            self.fp.seek(self.newsubfiletag_loc)
            self.writeTag(NewSubfileType, "long", 1, 2)
        self.fp.close()

    # Write a single tiff tag at current fp location
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

    import sys

    im = TiffWriter(sys.argv[1])

    frame_x = 200
    frame_y = 200
    frame = chr(10) * (frame_x * frame_y * 2)

    for i in range(5):
        frame = chr(i) * (frame_x * frame_y * 2)
        im.addFrame(frame, frame_x, frame_y)

    im.close()

#
# Write image IFD
#
#
#cur_loc = fp.tell()
#
## Settings (for the test image)
#num_tags = 15
#image_x = 60
#image_y = 60
#bytes_per_pixel = 2
#image_size = image_x*image_y*bytes_per_pixel
#software = "hal4000" + chr(0)
#datetime = "2012:05:28 11:45:22" + chr(0)
#
## Calculations
#ifd_end = cur_loc + 2 + num_tags*12 + 4
#software_offset = ifd_end + 2*8
#datetime_offset = software_offset + len(software)
#image_offset =  datetime_offset + len(datetime)
#
## number of tags
#fp.write(struct.pack("H", num_tags))
#
## Tags. These are (apparently) required to be in ascending order.
#
## NewSubfileType tag
#writeTag(fp, 254, "long", 1, 0)
#
## ImageWidth
#writeTag(fp, 256, "long", 1, image_x)
#
## ImageLength
#writeTag(fp, 257, "long", 1, image_y)
#
## BitsPerSample
#writeTag(fp, 258, "short", 1, 8*bytes_per_pixel)
#
## Compression
#writeTag(fp, 259, "short", 1, 1)
#
## PhotometricInterpretation
#writeTag(fp, 262, "short", 1, 1)
#
## StripOffsets
##writeTag(fp, 273, "long", 1, ifd_end)
#writeTag(fp, 273, "long", 1, image_offset)
#
## SamplesPerPixel
#writeTag(fp, 277, "short", 1, 1)
#
## RowsPerStrip
#writeTag(fp, 278, "long", 1, image_y)
#
## StripByteCounts
##writeTag(fp, 279, "long", 1, ifd_end + 4)
#writeTag(fp, 279, "long", 1, image_size)
#
## XResolution
#writeTag(fp, 282, "rational", 1, ifd_end)
#
## YResolution
#writeTag(fp, 283, "rational", 1, ifd_end + 8)
#
## ResolutionUnit
#writeTag(fp, 296, "short", 1, 1)
#
## Software
#writeTag(fp, 305, "ascii", len(software), software_offset)
#
## DateTime
#writeTag(fp, 306, "ascii", len(datetime), datetime_offset)
#
## Next IFD offset (4 bytes)
#fp.write(struct.pack("I", 0))
#
##
## Additional tag data
##
#
## strip offset (4 bytes)
##fp.write(struct.pack("I", image_offset))
#
## strip byte counts (4 bytes)
##fp.write(struct.pack("I", image_size))
#
## X resolution (8 bytes)
#fp.write(struct.pack("I", 1))
#fp.write(struct.pack("I", 1))
#
## Y resolution (8 bytes)
#fp.write(struct.pack("I", 1))
#fp.write(struct.pack("I", 1))
#
## Software (arb)
#fp.write(struct.pack(str(len(software)) + "s", software))
#
## DateTime (arb)
#fp.write(struct.pack(str(len(datetime)) + "s", datetime))
#
#
##
## Write the image.
##
#image = chr(10) * image_size
#fp.write(image)
#fp.close()
#


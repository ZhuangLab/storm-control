#!/usr/bin/python
#
# Image file writers for various formats.
#
# Hazen 5/12
#

import struct
import tiffwriter

try:
    import andor.formatconverters as fconv
except:
    print "failed to load andor.formatconverters."

#
# Return a list of the available movie formats.
#
def availableFileFormats():
    return [".dax", ".spe", ".tif"]

def createFileWriter(filetype, filename, parameters):
    if (filetype == ".dax"):
        return DaxFile(filename, parameters)
    elif (filetype == ".spe"):
        return SPEFile(filename, parameters)
    elif (filetype == ".tif"):
        return TIFFile(filename, parameters)
    else:
        print "Unknown output file format, defaulting to .dax"
        return DaxFile(filename, parameters)

#
# Inf writing function. We save one of these regardless of the
# output format of the data as it is a easy way to preserve
# the file meta-data.
#
def writeInfFile(file_class, stage_position, lock_target):
        fp = open(file_class.filename + ".inf", "w")
        p = file_class.parameters
        nl =  "\n"
        fp.write("information file for" + nl)
        fp.write(file_class.filename + p.filetype + nl)
        fp.write("machine name = " + p.setup_name + nl)
        fp.write("parameters file = " + p.parameters_file + nl)
        fp.write("shutters file = " + p.shutters + nl)
        if p.frame_transfer_mode:
            fp.write("CCD mode = frame-transfer" + nl)
        if p.want_big_endian:
            fp.write("data type = 16 bit integers (binary, big endian)" + nl)
        else:
            fp.write("data type = 16 bit integers (binary, little endian)" + nl)
        fp.write("frame dimensions = " + str(p.x_pixels) + " x " + str(p.y_pixels) + nl)
        fp.write("binning = " + str(p.x_bin) + " x " + str(p.y_bin) + nl)
        fp.write("frame size = " + str(p.x_pixels * p.y_pixels) + nl)
        fp.write("horizontal shift speed = " + str(p.hsspeed) + nl)
        fp.write("vertical shift speed = " + str(p.vsspeed) + nl)
        fp.write("EMCCD Gain = " + str(p.emccd_gain) + nl)
        fp.write("Preamp Gain = " + str(p.preampgain) + nl)
        fp.write("Exposure Time = " + str(p.exposure_value) + nl)
        fp.write("Frames Per Second = " + str(1.0/p.kinetic_value) + nl)
        fp.write("camera temperature (deg. C) = " + str(p.actual_temperature) + nl)
        fp.write("number of frames = " + str(file_class.frames) + nl)
        fp.write("camera head = " + str(p.head_model) + nl)

        #
        # If Insight3 sees the following block it will assume that the
        # acquisition software did not rotate the camera image. This is
        # useful on Prism2 because then the image as displayed by
        # Insight3 will have the same orientation as the image on the
        # camera. Not sure why Insight3 otherwise chooses to do its
        # own additional rotations.
        #
        if p.setup_name == "prism2":
            fp.write("hstart=" + str(p.x_start) + nl)
            fp.write("hend=" + str(p.x_end) + nl)
            fp.write("vstart=" + str(p.y_start) + nl)
            fp.write("vend=" + str(p.y_end) + nl)            
        else:
            fp.write("x_start = " + str(p.x_start) + nl)
            fp.write("x_end = " + str(p.x_end) + nl)
            fp.write("y_start = " + str(p.y_start) + nl)
            fp.write("y_end = " + str(p.y_end) + nl)

        fp.write("ADChannel = " + str(p.adchannel) + nl)
        fp.write("Stage X = {0:.2f}".format(stage_position[0]) + nl)
        fp.write("Stage Y = {0:.2f}".format(stage_position[1]) + nl)
        fp.write("Stage Z = {0:.2f}".format(stage_position[2]) + nl)
        fp.write("Lock Target = " + str(lock_target) + nl)
        fp.write("scalemax = " + str(p.scalemax) + nl)
        fp.write("scalemin = " + str(p.scalemin) + nl)
        fp.write("notes = " + str(p.notes) + nl)
        fp.close()

#
# Dax file writing class
#
class DaxFile:
    def __init__(self, filename, parameters):
        self.parameters = parameters
        self.filename = filename
        self.fp = open(filename + ".dax", "wb")
        self.frames = 0
        self.open = 1

    def saveFrame(self, frame):
        if self.parameters.want_big_endian:
            self.fp.write(fconv.LEtoBE(frame))
        else:
            self.fp.write(frame)            
        self.frames += 1
 
    def closeFile(self, stage_position, lock_target):
        self.fp.close()
        writeInfFile(self, stage_position, lock_target)
        self.open = 0

    def __del__(self):
        if self.open:
            self.closeFile()
        
#
# SPE file writing class
#
class SPEFile:
    def __init__(self, filename, parameters):
        self.parameters = parameters
        self.filename = filename
        self.fp = open(filename + ".spe", "wb")
        self.frames = 0
        self.open = 1
        
        # write header
        header = chr(0) * 4100
        self.fp.write(header)
        self.fp.seek(42)
        self.fp.write(struct.pack("h", parameters.x_pixels))
        self.fp.seek(656)
        self.fp.write(struct.pack("h", parameters.y_pixels))
        self.fp.seek(108)
        self.fp.write(struct.pack("h", 3))
        self.fp.seek(4100)

    def saveFrame(self, frame):
        self.fp.write(frame)
        self.frames += 1
 
    def closeFile(self, stage_position, lock_target):
        # write film length & close the file
        self.fp.seek(1446)
        self.fp.write(struct.pack("i", self.frames))
        self.fp.close()

        writeInfFile(self, stage_position, lock_target)
        self.open = 0

    def __del__(self):
        if self.open:
            self.closeFile()

#
# TIF file writing class
#
class TIFFile:
    def __init__(self, filename, parameters):
        self.parameters = parameters
        self.filename = filename
        self.frames = 0
        self.open = 1
        self.tif_writer = tiffwriter.TiffWriter(filename + ".tif",
                                                software = "hal4000")

    def saveFrame(self, frame):
        self.tif_writer.addFrame(frame,
                                 self.parameters.x_pixels,
                                 self.parameters.x_pixels)
        self.frames += 1
 
    def closeFile(self, stage_position, lock_target):
        self.tif_writer.close()
        writeInfFile(self, stage_position, lock_target)
        self.open = 0

    def __del__(self):
        if self.open:
            self.closeFile()


#
# Testing
# 

if __name__ == "__main__":
    from ctypes import *

    class Parameters:
        def __init__(self, x_pixels, y_pixels, x_bin, y_bin):
            self.x_pixels = x_pixels
            self.y_pixels = y_pixels
            self.x_bin = x_bin
            self.y_bin = y_bin

    parameters = Parameters(100, 100, 1, 1)
    daxfile = DaxFile("test", parameters)
    frame = create_string_buffer(parameters.x_pixels * parameters.y_pixels)
    daxfile.saveFrame(frame)
    daxfile.closeFile()


#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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
 

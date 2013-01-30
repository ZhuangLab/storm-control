#!/usr/bin/python
#
# Image file writers for various formats.
#
# Hazen 5/12
#

import copy
import struct
import tiffwriter

try:
    import andor.formatconverters as fconv
except:
    print "failed to load andor.formatconverters."

#
# Return a list of the available movie formats.
#
def availableFileFormats(ui_mode):
    if (ui_mode == "dual"):
        return [".dax", ".dcf", ".spe", ".tif"]
    else:
        return [".dax", ".spe", ".tif"]

def createFileWriter(filetype, filename, parameters, cameras):
    if (filetype == ".dax"):
        return DaxFile(filename, parameters, cameras)
    elif (filetype == ".dcf"):
        return DualCameraFormatFile(filename, parameters, cameras)
    elif (filetype == ".spe"):
        return SPEFile(filename, parameters, cameras)
    elif (filetype == ".tif"):
        return TIFFile(filename, parameters, cameras)
    else:
        print "Unknown output file format, defaulting to .dax"
        return DaxFile(filename, parameters, cameras)

def getCameraSize(parameters, camera_name):
    if (hasattr(parameters, camera_name)):
        camera_obj = getattr(parameters, camera_name)
        x_pixels = camera_obj.x_pixels
        y_pixels = camera_obj.y_pixels
    else:
        x_pixels = parameters.x_pixels
        y_pixels = parameters.y_pixels
    return [x_pixels, y_pixels]

#
# Inf writing function. We save one of these regardless of the
# output format of the data as it is a easy way to preserve
# the file meta-data.
#
def writeInfFile(filename, filetype, number_frames, parameters, camera, stage_position, lock_target):
    c = camera
    fp = open(filename[0:-len(filetype)] + ".inf", "w")
    nl =  "\n"
    p = parameters

    # General info
    fp.write("information file for" + nl)
    fp.write(filename + nl)
    fp.write("machine name = " + p.setup_name + nl)
    fp.write("parameters file = " + p.parameters_file + nl)
    fp.write("shutters file = " + p.shutters + nl)
    if p.want_big_endian:
        fp.write("data type = 16 bit integers (binary, big endian)" + nl)
    else:
        fp.write("data type = 16 bit integers (binary, little endian)" + nl)
    fp.write("number of frames = " + str(number_frames) + nl)

    # Camera related
    fp.write("frame size = " + str(c.x_pixels * c.y_pixels) + nl)
    fp.write("frame dimensions = " + str(c.x_pixels) + " x " + str(c.y_pixels) + nl)
    fp.write("binning = " + str(c.x_bin) + " x " + str(c.y_bin) + nl)
    if c.frame_transfer_mode:
        fp.write("CCD mode = frame-transfer" + nl)
    fp.write("horizontal shift speed = " + str(c.hsspeed) + nl)
    fp.write("vertical shift speed = " + str(c.vsspeed) + nl)
    fp.write("EMCCD Gain = " + str(c.emccd_gain) + nl)
    fp.write("Preamp Gain = " + str(c.preampgain) + nl)
    fp.write("Exposure Time = " + str(c.exposure_value) + nl)
    fp.write("Frames Per Second = " + str(1.0/c.kinetic_value) + nl)
    fp.write("camera temperature (deg. C) = " + str(c.actual_temperature) + nl)
    fp.write("camera head = " + str(c.head_model) + nl)
    fp.write("ADChannel = " + str(c.adchannel) + nl)
    fp.write("scalemax = " + str(c.scalemax) + nl)
    fp.write("scalemin = " + str(c.scalemin) + nl)

    fp.write("x_start = " + str(c.x_start) + nl)
    fp.write("x_end = " + str(c.x_end) + nl)
    fp.write("y_start = " + str(c.y_start) + nl)
    fp.write("y_end = " + str(c.y_end) + nl)

    # Additional info
    fp.write("Stage X = {0:.2f}".format(stage_position[0]) + nl)
    fp.write("Stage Y = {0:.2f}".format(stage_position[1]) + nl)
    fp.write("Stage Z = {0:.2f}".format(stage_position[2]) + nl)
    fp.write("Lock Target = " + str(lock_target) + nl)
    fp.write("notes = " + str(p.notes) + nl)
    fp.close()

#def writeInfFile(file_class, stage_position, lock_target):
#        fp = open(file_class.filename + ".inf", "w")
#        p = file_class.parameters
#        nl =  "\n"

#
# Generic file writing class
#

class GenericFile:
    def __init__(self, filename, parameters, cameras, extension, want_fp = True):
        self.cameras = cameras
        self.parameters = parameters
        self.open = True

        self.filenames = []
        self.file_ptrs = []
        self.number_frames = []
        if (len(cameras) > 1):
            for i in range(len(cameras)):
                fname = filename + "_cam" + str(i+1) + "." + extension
                self.filenames.append(fname)
                if want_fp:
                    self.file_ptrs.append(open(fname, "wb"))
                self.number_frames.append(0)
        else:
            fname = filename + "." + extension
            self.filenames.append(fname)
            if want_fp:
                self.file_ptrs.append(open(fname, "wb"))
            self.number_frames.append(0)

    def closeFile(self, stage_position, lock_target):
        
        # Close the files.
        if (len(self.file_ptrs)>0):
            for fp in self.file_ptrs:
                fp.close()

        # Write the inf files.
        for i in range(len(self.filenames)):
            if (hasattr(self.parameters, self.cameras[i])):
                camera = getattr(self.parameters, self.cameras[i])
            else:
                camera = self.parameters
            writeInfFile(self.filenames[i],
                         self.parameters.filetype,
                         self.number_frames[i],
                         self.parameters,
                         camera,
                         stage_position,
                         lock_target)

        self.open = False

    def totalFilmSize(self):
        total_size = 0.0
        for i in range(len(self.filenames)):
            if (hasattr(self.parameters, self.cameras[i])):
                temp = getattr(self.parameters, self.cameras[i])
            else:
                temp = self.parameters
            total_size += self.number_frames[i] * temp.bytesPerFrame * 0.000000953674
        return total_size

    def __del__(self):
        if self.open:
            self.closeFile()

#
# Dax file writing class
#
class DaxFile(GenericFile):
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "dax")

    def saveFrame(self, frame):
        for i in range(len(self.cameras)):
            if (frame.which_camera == self.cameras[i]):
                if self.parameters.want_big_endian:
                    self.file_ptrs[i].write(fconv.LEtoBE(frame.data))
                else:
                    self.file_ptrs[i].write(frame.data)

                self.number_frames[i] += 1

#
# Dual camera format writing class
#
# This is just the dax format with the camera number encoded into the
# first pixel of the image. It is useful because writing two files
# at once at a high data rate can overwhelm a hard-drive.
# 
class DualCameraFormatFile(GenericFile):
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "dax")

    def saveFrame(self, frame):
        camera_int = int(frame.which_camera[6:])-1
        temp = chr(camera_int) + chr(camera_int) + copy.copy(frame.data[2:])
        if self.parameters.want_big_endian:
            self.file_ptrs[0].write(fconv.LEtoBE(temp))
        else:
            self.file_ptrs[0].write(temp)
        self.number_frames[0] += 1

#
# SPE file writing class
#
class SPEFile(GenericFile):
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "spe")
        
        # write headers
        for i in range(len(self.file_ptrs)):
            [x_pixels, y_pixels] = getCameraSize(parameters, self.cameras[i])
            fp = self.file_ptrs[i]
            header = chr(0) * 4100
            fp.write(header)
            fp.seek(42)
            fp.write(struct.pack("h", x_pixels))
            fp.seek(656)
            fp.write(struct.pack("h", y_pixels))
            fp.seek(108)
            fp.write(struct.pack("h", 3))
            fp.seek(4100)

    def saveFrame(self, frame):
        for i in range(len(self.cameras)):
            if (frame.which_camera == self.cameras[i]):
                self.file_ptrs[i].write(frame.data)
                
                self.number_frames[i] += 1
 
    def closeFile(self, stage_position, lock_target):
        # write film length & close the file
        for i in range(len(self.file_ptrs)):
            self.file_ptrs[i].seek(1446)
            self.file_ptrs[i].write(struct.pack("i", self.number_frames[i]))

        GenericFile.closeFile(self, stage_position, lock_target)

#
# TIF file writing class
#
class TIFFile(GenericFile):
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "tif", want_fp = False)

        self.tif_writers = []
        for i in range(len(cameras)):
            tif_writer = tiffwriter.TiffWriter(self.filenames[i],
                                               software = "hal4000")
            self.tif_writers.append(tif_writer)

    def saveFrame(self, frame):
        for i in range(len(self.cameras)):
            if (frame.which_camera == self.cameras[i]):
                [x_pixels, y_pixels] = getCameraSize(self.parameters, self.cameras[i])
                self.tif_writers[i].addFrame(frame.data, x_pixels, y_pixels)

                self.number_frames[i] += 1
 
    def closeFile(self, stage_position, lock_target):
        for writer in self.tif_writers:
            writer.close()
        GenericFile.closeFile(self, stage_position, lock_target)

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
 

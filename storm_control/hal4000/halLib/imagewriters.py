#!/usr/bin/env python
"""
Image file writers for various formats.

Hazen 03/17
"""

import copy
import datetime
import struct

import storm_control.sc_library.hgit as hgit
import storm_control.sc_library.parameters as params

import storm_control.hal4000.camera.feeds as feeds
import storm_control.hal4000.halLib.tiffwriter as tiffwriter

# Get the version of the software.
software_version = hgit.getVersion()

def availableFileFormats():
    """
    Return a list of the available movie formats.
    """
    return [".dax", ".spe", ".tif"]

def createFileWriter(feed_params, film_settings):
    """
    This is convenience function which creates the appropriate file writer
    based on the filetype.
    """
    ft = film_settings["filetype"]
    if (ft == ".dax"):
        return DaxFile(feed_params = feed_params, film_settings = film_settings)
    elif (ft == ".spe"):
        return SPEFile(feed_params = feed_params, film_settings = film_settings)
    elif (ft == ".tif"):
        return TIFFile(feed_params = feed_params, film_settings = film_settings)
    else:
        print("Unknown output file format, defaulting to .dax")
        return DaxFile(feed_params = feed_params, film_settings = film_settings)

## writeInfFile
#
# Inf writing function. We save one of these regardless of the
# output format of the data as it is a easy way to preserve
# the file meta-data.
#
# @param filename The name of the movie file.
# @param number_frames The number of frames in the movie.
# @param parameters A parameters object.
# @param camera The camera sub-object of a parameters object.
# @param stage_position The stage position, [stage x, stage y, stage z].
# @param lock_target The focus lock target.
#
def writeInfFile(filename, number_frames, parameters, camera):
    c = camera
    fp = open(filename + ".inf", "w")
    nl = "\n"
    p = parameters

    # General info
    fp.write("information file for" + nl)
    fp.write(filename + nl)
    fp.write("software version = " + software_version + nl)
    fp.write("machine name = " + p.get("setup_name") + nl)
    fp.write("parameters file = " + p.get("parameters_file") + nl)
    fp.write("shutters file = " + p.get("illumination.shutters", "NA") + nl)
    if p.get("film.want_big_endian"):
        fp.write("data type = 16 bit integers (binary, big endian)" + nl)
    else:
        fp.write("data type = 16 bit integers (binary, little endian)" + nl)
    fp.write("number of frames = " + str(number_frames) + nl)

    # Camera related
    fp.write("frame size = " + str(c.get("x_pixels") * c.get("y_pixels")) + nl)
    fp.write("frame dimensions = " + str(c.get("x_pixels")) + " x " + str(c.get("y_pixels")) + nl)
    fp.write("binning = " + str(c.get("x_bin")) + " x " + str(c.get("y_bin")) + nl)

    # Only save the following for actual cameras.
    if not c.has("source"):
        if hasattr(c, "frame_transfer_mode") and c.frame_transfer_mode:
            fp.write("CCD mode = frame-transfer" + nl)
        fp.write("horizontal shift speed = " + str(c.get("hsspeed", "NA")) + nl)
        fp.write("vertical shift speed = " + str(c.get("vsspeed", "NA")) + nl)
        fp.write("EMCCD Gain = " + str(c.get("emccd_gain", "NA")) + nl)
        fp.write("Preamp Gain = " + str(c.get("preampgain", "NA")) + nl)
        fp.write("Exposure Time = " + str(c.get("exposure_value", "NA")) + nl)
        fp.write("Frames Per Second = " + str(1.0/c.get("cycle_value", "NA")) + nl)
        fp.write("camera temperature (deg. C) = " + str(c.get("actual_temperature", "NA")) + nl)
        fp.write("camera head = " + str(c.get("head_model", "NA")) + nl)
        fp.write("ADChannel = " + str(c.get("adchannel", "NA")) + nl)
        fp.write("scalemax = " + str(c.get("scalemax")) + nl)
        fp.write("scalemin = " + str(c.get("scalemin")) + nl)

        fp.write("x_start = " + str(c.get("x_start")) + nl)
        fp.write("x_end = " + str(c.get("x_end")) + nl)
        fp.write("y_start = " + str(c.get("y_start")) + nl)
        fp.write("y_end = " + str(c.get("y_end")) + nl)

        # Additional info
        stage_pos = p.get("acquisition.stage_position").split(",")
        fp.write("Stage X = " + stage_pos[0] + nl)
        fp.write("Stage Y = " + stage_pos[1] + nl)
        fp.write("Stage Z = " + stage_pos[2] + nl)
        fp.write("Lock Target = " + str(p.get("acquisition.lock_target")) + nl)
         
    fp.write("notes = " + str(p.get("film.notes")) + nl)
    fp.close()

#def writeInfFile(file_class, stage_position, lock_target):
#        fp = open(file_class.filename + ".inf", "w")
#        p = file_class.parameters
#        nl =  "\n"



class BaseFileWriter(object)

    def __init__(self, feed_params = None, film_settings = None, **kwds):
        super().__init__(**kwds)
        self.feed_params = feed_params
        self.film_settings = film_settings

        self.frame_size = self.feed_params["bytes_per_frame"]
        self.number_frames = 0

        # Figure out the filename.
        self.basename = self.film_settings["basename"]
        if len(self.feed_params["extension"] != 0):
            self.basename += "_" + self.feed_params["extension"]
        self.filename = self.basename + "." + self.film_settings["filetype"]

    def saveFrame(self, frame):
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

        w = str(self.feed_params["x_pixels"])
        h = str(self.feed_params["y_pixels"])
        with open(self.basename + ".inf", "w") as inf_fp:
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


class SPEFile(GenericFile):
    """
    SPE file writing class.

    FIXME: This has not been tested, could be broken..
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.fp = open(self.filename, "wb")
        
        # Write header information.
            [x_pixels, y_pixels] = getCameraSize(parameters, self.feed_names[i])

        header = chr(0) * 4100
        self.fp.write(header)

        # NOSCAN
        self.fp.seek(34)
        self.fp.write(struct.pack("h", -1))

        # FACCOUNT (width)
        self.fp.seek(42)
        self.fp.write(struct.pack("h", self.feed_params["x_pixels"]))

        # DATATYPE
        self.fp.seek(108)
        self.fp.write(struct.pack("h", 3))
           
        # LNOSCAN
        self.fp.seek(664)
        self.fp.write(struct.pack("h", -1))

        # STRIPE (height)
        self.fp.seek(656)
        self.fp.write(struct.pack("h", self.feed_params["y_pixels"]))

        self.fp.seek(4100)

    def saveFrame(self, frame):
        np_data = frame.getData()
        np_data.tofile(self.file_ptrs[index])
        return super().saveFrame()

    def closeFile(self):
        self.fp.seek(1446)
        self.fp.write(struct.pack("i", self.number_frames))


class TIFFile(GenericFile):
    """
    TIF file writing class. Note that this is a normal tif file format
    and not a big tif format so the maximum size is limited to 4GB
    more or less.
    """

    ## __init__
    #
    # Creates the tif writer(s) for saving in tif format.
    #
    # @param filename The name of the movie file (without an extension).
    # @param parameters A parameters object.
    # @param cameras A python array of camera names, e.g. ["camera1"].
    #
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "tif", want_fp = False)
        
        self.tif_writers = []
        for i in range(len(cameras)):

            # Determine pixel size (if possible).
            pixel_size = 1.0
            cur_obj = parameters.get("mosaic.objective", False)
            if cur_obj:
                pixel_size = float(parameters.get("mosaic." + cur_obj).split(",")[1])
            tif_writer = tiffwriter.TiffWriter(self.filenames[i],
                                               software = "hal4000",
                                               x_pixel_size = pixel_size,
                                               y_pixel_size = pixel_size)
            self.tif_writers.append(tif_writer)

    ## saveFrame
    #
    # @param frame A frame object.
    #
    def saveFrame(self, frame):
        if frame.which_camera in self.feed_names:
            index = self.feed_names.index(frame.which_camera)
            [x_pixels, y_pixels] = getCameraSize(self.parameters, self.feed_names[index])
            self.tif_writers[index].addFrame(frame.getData(), x_pixels, y_pixels)
            
            self.number_frames[index] += 1

    ## closeFile
    #
    # Closes the tif file writers.
    #
    def closeFile(self):
        for writer in self.tif_writers:
            writer.close()
        GenericFile.closeFile(self)

#
# Testing
# 

if __name__ == "__main__":
    import ctypes

    class Parameters:
        def __init__(self, x_pixels, y_pixels, x_bin, y_bin):
            self.x_pixels = x_pixels
            self.y_pixels = y_pixels
            self.x_bin = x_bin
            self.y_bin = y_bin

    parameters = Parameters(100, 100, 1, 1)
    daxfile = DaxFile("test", parameters)
    frame = ctypes.create_string_buffer(parameters.get("x_pixels") * parameters.get("y_pixels"))
    daxfile.saveFrame(frame)
    daxfile.closeFile()


#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
 

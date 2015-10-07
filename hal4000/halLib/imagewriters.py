#!/usr/bin/python
#
## @file
#
# Image file writers for various formats.
#
# Hazen 02/14
#

import copy
import struct
import tiffwriter

import sc_library.hgit as hgit
import sc_library.parameters as params

import camera.feeds as feeds

# Get the version of the software.
software_version = hgit.getVersion()

## availableFileFormats
#
# Return a list of the available movie formats.
#
# @return A python list of file extensions (".dax", ".spe", etc..).
#
def availableFileFormats(ui_mode):
    if (ui_mode == "dual"):
        return [".dax", ".dcf", ".spe", ".tif"]
    else:
        return [".dax", ".spe", ".tif"]

## createFileWriter
#
# This is convenience function which creates the appropriate file writer
# based on the filetype.
#
# @param filetype A string specifying one of the available file formats, e.g. ".dax", ".spe", etc.
# @param filename The name of the file.
# @param parameters A parameters object.
# @param cameras A array of camera names, such as ["camera1"].
#
# @return A file writer object.
#
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

## getCameraSize
#
# Returns the AOI of the camera specified by camera_name
#
# @param parameters A parameters object.
# @param feed_name The name of the feed, e.g. "camera1".
#
# @return [x size (pixels), y size (pixels)]
#
def getCameraSize(parameters, feed_name):
    if feeds.isCamera(feed_name):
        feed_obj = parameters.get(feed_name, parameters)
    else:
        feed_obj = parameters.get("feeds." + feed_name, parameters)        
    return [feed_obj.get("x_pixels"), feed_obj.get("y_pixels")]

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
        fp.write("Stage X = {0:.2f}".format(p.get("acquisition.stage_position")[0]) + nl)
        fp.write("Stage Y = {0:.2f}".format(p.get("acquisition.stage_position")[1]) + nl)
        fp.write("Stage Z = {0:.2f}".format(p.get("acquisition.stage_position")[2]) + nl)
        fp.write("Lock Target = " + str(p.get("acquisition.lock_target")) + nl)
         
    fp.write("notes = " + str(p.get("film.notes")) + nl)
    fp.close()

#def writeInfFile(file_class, stage_position, lock_target):
#        fp = open(file_class.filename + ".inf", "w")
#        p = file_class.parameters
#        nl =  "\n"


## GenericFile
#
# Generic file writing class
#
class GenericFile:

    ## __init__
    #
    # @param filename The name of the movie file (without an extension).
    # @param parameters A parameters object.
    # @param feed_names A python array of feed names, e.g. ["camera1"].
    # @param extension The movie file extension (".spe", ".dax", etc.).
    # @param want_fp (Optional) Create file pointer(s) for saving the movie.
    #
    def __init__(self, filename, parameters, feed_names, extension, want_fp = True):
        self.feed_names = feed_names
        self.is_open = True
        self.parameters = parameters.copy()
        self.parameters.set("acquisition", params.StormXMLObject([]))
        
        # FIXME: different cameras could have different lock targets.
        self.parameters.set("acquisition.lock_target", 0.0)
        self.parameters.set("acquisition.spot_counts", "NA")
        self.parameters.set("acquisition.stage_position", [0.0, 0.0, 0.0])

        self.filename = filename
        self.filenames = []
        self.file_ptrs = []
        self.number_frames = []

        # Just return if there is nothing to save.
        if (len(self.feed_names) == 0):
            return
        
        if (len(self.feed_names) > 1):
            
            # Figure out if there is more than one camera.
            n_cameras = 0
            for feed_name in self.feed_names:
                if feeds.isCamera(feed_name):
                    n_cameras += 1
            
            for feed_name in self.feed_names:

                # Only stick the camera name into the file if there is more than one camera.
                if feeds.isCamera(feed_name):
                    if (n_cameras > 1):
                        fname = filename + "_" + feed_name + "." + extension
                    else:
                        fname = filename + "." + extension
                else:
                    fname = filename + "_" + feed_name + "." + extension
                    
                self.filenames.append(fname)
                if want_fp:
                    self.file_ptrs.append(open(fname, "wb"))
                self.number_frames.append(0)
        else:
            feed_name = self.feed_names[0]
            if feeds.isCamera(feed_name):
                fname = filename + "." + extension
            else:
                fname = filename + "_" + feed_name + "." + extension
            self.filenames.append(fname)
            if want_fp:
                self.file_ptrs.append(open(fname, "wb"))
            self.number_frames.append(0)

    ## closeFile
    #
    # Close the file pointers (if any) and write the .inf file.
    #
    def closeFile(self):
        
        # Close the files.
        if (len(self.file_ptrs)>0):
            for fp in self.file_ptrs:
                fp.close()

        # Write the parameters XML and .inf files.
        for i in range(len(self.filenames)):
            if feeds.isCamera(self.feed_names[i]):
                camera = self.parameters.get(self.feed_names[i], self.parameters)
            else:
                camera = self.parameters.get("feeds." + self.feed_names[i], self.parameters)
                
            filename = self.filenames[i][0:-len(self.parameters.get("film.filetype"))]
            writeInfFile(filename,
                         self.number_frames[i],
                         self.parameters,
                         camera)

            # Save the parameters, but only for the cameras.
            if feeds.isCamera(self.feed_names[i]):            
                self.parameters.set("acquisition.camera", "camera" + str(i+1))
                self.parameters.set("acquisition.number_frames", self.number_frames[i])
                self.parameters.saveToFile(filename + ".xml")

        self.is_open = False

    ## getFilmLength()
    #
    # @return The film's length in number of frames (per camera).
    #
    def getFilmLength(self):
        return self.number_frames

    ## getLockTarget()
    #
    # @return The film's lock target.
    #
    def getLockTarget(self):
        return self.parameters.get("acquisition.lock_target")

    ## getParameters()
    #
    # @return The film parameters.
    #
    def getParameters(self):
        return self.parameters
    
    ## getSpotCounts()
    #
    # @return The film's spot counts.
    #
    def getSpotCounts(self):
        return self.parameters.get("acquisition.spot_counts")

#    ## setLockTarget()
#    #
#    # @param lock_target The film's lock target.
#    #
#    def setLockTarget(self, lock_target):
#        self.lock_target = lock_target
#
#    ## setSpotCounts()
#    #
#    # @param spot_counts The film's spot counts (this is saved as a string).
#    #
#    def setSpotCounts(self, spot_counts):
#        self.spot_counts = spot_counts
#
#    ## setStagePosition()
#    #
#    # @param stage_position The new stage position.
#    #
#    def setStagePosition(self, stage_position):
#        self.stage_position = stage_position

    ## totalFilmSize
    #
    # @return The total size of the film taken so far in mega-bytes.    
    #
    def totalFilmSize(self):
        total_size = 0.0
        for i in range(len(self.filenames)):
            if feeds.isCamera(self.feed_names[i]):
                temp = self.parameters.get(self.feed_names[i])
            else:
                temp = self.parameters.get("feeds." + self.feed_names[i])
            total_size += self.number_frames[i] * temp.get("bytes_per_frame") * 0.000000953674
        return total_size

    ## __del__
    #
    # Clean things up if this object is deleted.
    #
    def __del__(self):
        if self.is_open:
            self.closeFile()
            

## DaxFile
#
# Dax file writing class.
#
class DaxFile(GenericFile):

    ## __init__
    #
    # @param filename The name of the movie file (without an extension).
    # @param parameters A parameters object.
    # @param cameras A python array of camera names, e.g. ["camera1"].
    #
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "dax")

    ## saveFrame
    #
    # Saves a frame. If we have two cameras then this first figures
    # out which of the two output files to save it to.
    #
    # @param frame A frame object.
    #
    def saveFrame(self, frame):
        if frame.which_camera in self.feed_names:
            index = self.feed_names.index(frame.which_camera)
            np_data = frame.getData()
            if self.parameters.get("film.want_big_endian"):
                np_data = np_data.byteswap()
                np_data.tofile(self.file_ptrs[index])
            else:
                np_data.tofile(self.file_ptrs[index])
            
            self.number_frames[index] += 1


## DualCameraFormatFile
#
# Dual camera format writing class.
#
# This is just the dax format with the camera number encoded into the
# first pixel of the image. It is useful because writing two files
# at once at a high data rate can overwhelm a hard-drive.
# 
class DualCameraFormatFile(GenericFile):

    ## __init__
    #
    # @param filename The name of the movie file (without an extension).
    # @param parameters A parameters object.
    # @param cameras A python array of camera names, e.g. ["camera1"].
    #
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "dax")

    ## saveFrame
    #
    # Saves a frame. In this format the camera information (i.e. which
    # camera the frame is from) is encoded into the first pixel of the picture.
    #
    # @param frame A frame object.
    #
    def saveFrame(self, frame):
        np_data = frame.getData().copy()
        np_data[0] = int(frame.which_camera[-1:])-1
        if self.parameters.get("film.want_big_endian"):
            np_data.tofile(self.file_ptrs[0]).byteswap()
        else:
            np_data.tofile(self.file_ptrs[0])
        self.number_frames[0] += 1

        
## SPEFile
#
# SPE file writing class.
#
class SPEFile(GenericFile):

    ## __init__
    #
    # @param filename The name of the movie file (without an extension).
    # @param parameters A parameters object.
    # @param cameras A python array of camera names, e.g. ["camera1"].
    #
    def __init__(self, filename, parameters, cameras):
        GenericFile.__init__(self, filename, parameters, cameras, "spe")
        
        # write headers
        for i in range(len(self.file_ptrs)):
            [x_pixels, y_pixels] = getCameraSize(parameters, self.feed_names[i])
            fp = self.file_ptrs[i]
            header = chr(0) * 4100
            fp.write(header)

            # NOSCAN
            fp.seek(34)
            fp.write(struct.pack("h", -1))

            # FACCOUNT (width)
            fp.seek(42)
            fp.write(struct.pack("h", x_pixels))

            # DATATYPE
            fp.seek(108)
            fp.write(struct.pack("h", 3))
           
            # LNOSCAN
            fp.seek(664)
            fp.write(struct.pack("h", -1))

            # STRIPE (height)
            fp.seek(656)
            fp.write(struct.pack("h", y_pixels))

            fp.seek(4100)

    ## saveFrame
    #
    # @param frame A frame object.
    #
    def saveFrame(self, frame):
        if frame.which_camera in self.feed_names:
            index = self.feed_names.index(frame.which_camera)
            np_data = frame.getData()
            np_data.tofile(self.file_ptrs[index])
            self.number_frames[index] += 1

    ## closeFile
    #
    # Writes the file size into the header part of the spe file and
    # then closes the file.
    #
    def closeFile(self):
        # write film length & close the file
        for i in range(len(self.file_ptrs)):
            self.file_ptrs[i].seek(1446)
            self.file_ptrs[i].write(struct.pack("i", self.number_frames[i]))

        GenericFile.closeFile(self)
        

## TIFFile
#
# TIF file writing class. Note that this is a normal tif file format
# and not a big tif format so the maximum size is limited to 4GB
# more or less.
#
class TIFFile(GenericFile):

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
            tif_writer = tiffwriter.TiffWriter(self.filenames[i],
                                               software = "hal4000")
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
    from ctypes import *

    class Parameters:
        def __init__(self, x_pixels, y_pixels, x_bin, y_bin):
            self.x_pixels = x_pixels
            self.y_pixels = y_pixels
            self.x_bin = x_bin
            self.y_bin = y_bin

    parameters = Parameters(100, 100, 1, 1)
    daxfile = DaxFile("test", parameters)
    frame = create_string_buffer(parameters.get("x_pixels") * parameters.get("y_pixels"))
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
 

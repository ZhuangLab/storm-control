#!/usr/bin/python
#
## @file
#
# Classes that handles reading dax movie files. This is
# used by the Steve program. A more sophisticated version
# of this module is available in the Zhuang lab storm-analysis
# project on github (sa_library/datareader.py). The duplication
# here is to avoid the dependency.
#
# Hazen 12/09
#

import numpy
import os
import re


#
# Utility functions
#

## undoInsightTransformStorm2
#
# Not used?
#
# @return The original image rotated 90d and flipped horizontally.
#
def undoInsightTransformStorm2(original):
    return numpy.fliplr(numpy.rot90(original))

## undoInsightTransformStorm3
#
# Not used?
#
# @return The original image rotated 180d.
#
def undoInsightTransformStorm3(original):
    return numpy.rot90(numpy.rot90(original))


## Reader
#
# The superclass containing those functions that are common to both dax 
# and spe processing. However there is no spe processing implemented
# as yet.
#
class Reader:

    ## __del__
    #
    # Close the file on cleanup.
    #
    def __del__(self):
        if self.fileptr:
            self.fileptr.close()

    ## averageFrame
    #
    # average multiple frames in a movie.
    #
    # @param start (Optional) The starting frame for averaging.
    # @param end (Optional) The ending frame for averaging.
    #
    def averageFrames(self, start = False, end = False):
        if (not start):
            start = 0
        if (not end):
            end = self.number_frames 

        length = end - start
        average = numpy.zeros((self.image_width, self.image_height), numpy.float)
        for i in range(length):
            average += self.loadAFrame(i + start)
            
        average = average/float(length)
        return average

    ## closeFilePtr
    #
    # Closes the (dax) file pointer.
    #
    def closeFilePtr(self):
        if self.fileptr:
            self.fileptr.close()

    ## filmFileName
    #
    # @return The film name.
    #
    def filmFilename(self):
        return self.filename

    ## filmLocation
    #
    # @return The picture x,y location, if available.
    #
    def filmLocation(self):
        if hasattr(self, "stage_x"):
            return [self.stage_x, self.stage_y]
        else:
            return ["NA", "NA"]

    ## filmParameters
    #
    # @return The film parameters file, if available.
    #
    def filmParameters(self):
        if hasattr(self, "parameters"):
            return self.parameters
        else:
            return "NA"

    ## filmSize
    #
    # @return [image width, image height, number of frames].
    #
    def filmSize(self):
        return [self.image_width, self.image_height, self.number_frames]

    ## lockTarget
    #
    # @return The film focus lock target.
    #
    def lockTarget(self):
        if hasattr(self, "lock_target"):
            return self.lock_target
        else:
#            return "NA"
            return 0.0

    ## filmScale
    #
    # Returns the display scale used to display the film when the picture was taken.
    #
    # @return [display minimum, display maximum]
    #
    def filmScale(self):
        if hasattr(self, "scalemin") and hasattr(self, "scalemax"):
            return [self.scalemin, self.scalemax]
        else:
            return [100, 2000]

## DaxReader
#
# The dax file reader class.
#
class DaxReader(Reader):

    ## __init__
    #
    # dax file specific initialization, mostly this is parsing the associated .inf file.
    #
    # @param filename The name of the dax file to load.
    # @param verbose (Optional) True/False verbose mode.
    #
    def __init__(self, filename, verbose = False):
        # save the filenames
        self.filename = filename
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
        stagex_re = re.compile(r'Stage X = ([\d\.\-]+)')
        stagey_re = re.compile(r'Stage Y = ([\d\.\-]+)')
        lock_target_re = re.compile(r'Lock Target = ([\d\.\-]+)')
        scalemax_re = re.compile(r'scalemax = ([\d\.\-]+)')
        scalemin_re = re.compile(r'scalemin = ([\d\.\-]+)')
        parameters_re = re.compile(r'parameters file = (.+)')

        inf_file = open(self.inf_filename, "r")
        while 1:
            line = inf_file.readline()
            if not line: break
            m = size_re.match(line)
            if m:
                self.image_height = int(m.group(1))
                self.image_width = int(m.group(2))
            m = length_re.match(line)
            if m:
                self.number_frames = int(m.group(1))
            m = endian_re.search(line)
            if m:
                if m.group(1) == "big":
                    self.bigendian = 1
                else:
                    self.bigendian = 0
            m = stagex_re.match(line)
            if m:
                self.stage_x = float(m.group(1))
            m = stagey_re.match(line)
            if m:
                self.stage_y = float(m.group(1))
            m = lock_target_re.match(line)
            if m:
                self.lock_target = float(m.group(1))
            m = scalemax_re.match(line)
            if m:
                self.scalemax = int(m.group(1))
            m = scalemin_re.match(line)
            if m:
                self.scalemin = int(m.group(1))
            m = parameters_re.match(line)
            if m:
                self.parameters = m.group(1)

        inf_file.close()

        # set defaults, probably correct, but warn the user 
        # that they couldn't be determined from the inf file.
        if not self.image_height:
            print "Could not determine image size, assuming 256x256."
            self.image_height = 256
            self.image_width = 256

        # open the dax file
        if os.path.exists(filename):
            self.fileptr = open(filename, "rb")
        else:
            self.fileptr = 0
            if verbose:
                print "dax data not found", filename

    ## loadAFrame
    #
    # Loads a frame and use it to create a numpy array. Return the transpose of this array.
    #
    # @param frame_number The frame number of the frame to load (zero indexed).
    #
    def loadAFrame(self, frame_number):
        if self.fileptr:
            assert frame_number >= 0, "frame_number must be greater than or equal to 0"
            assert frame_number < self.number_frames, "frame number must be less than " + str(self.number_frames)
            self.fileptr.seek(frame_number * self.image_height * self.image_width * 2)
            image_data = numpy.fromfile(self.fileptr,dtype='int16', count = self.image_height * self.image_width)
            image_data = numpy.transpose(numpy.reshape(image_data, [self.image_width, self.image_height]))
            if self.bigendian:
                image_data.byteswap(True)
            return image_data


#!/usr/bin/python
#
## @file
#
# Handles "communication" with the THUM temperature reader.
#
# Hazen 3/09
#

import time

## Thum
#
# "Communicates" with a THUM temperature reader. The THUM reader periodically
# updates a file with the current temperature, etc. reading. This just reads
# that file every 5 seconds and copies the result into a new file to keep a 
# record of changes that occured during filming.
#
class Thum():

    ## __init__
    #
    # Sets some object default variables.
    #
    def __init__(self):
        self.reading = ""
        self.last_sample_time = 0
        self.fp = 0
        self.data = 0

    ## newFrame
    #
    # Called when we get new frame data from the camera. If it has been
    # 5 seconds since the last time we checked the data from the THUM
    # then we update self.data. The current value of self.data is
    # saved for every frame.
    #
    # @param frame A frame object.
    #
    def newFrame(self, frame):
        if self.fp and frame.master:
            current_time = time.time()
            if (current_time - self.last_sample_time) > 5.0:
                self.last_sample_time = current_time
                data_fp = open("C:/users/Wenqin/THUM/html/temprh")
                data = data_fp.readline()
                data_fp.close()
                data = data.split("|")
                self.data = ""
                for datum in data:
                    self.data += str(datum) + ","
                self.data = self.data[:-1]
            self.fp.write(str(frame.number+1) + "," + self.data)

    ## startThum
    #
    # Called at the start of filming.
    #
    # @param filename The name of the movie.
    #
    def startThum(self, filename):
        self.fp = open(filename + ".log", "w")

    ## stopThum
    #
    # Called at the end of filming.
    #
    def stopThum(self):
        if self.fp:
            self.fp.close()
            self.fp = 0


#
# Testing
#

if __name__ == "__main__":
    thum = Thum()
    thum.startThum("test.txt")
    thum.newData()
    for i in range(6):
        time.sleep(5)
        print i
        thum.newData()
    thum.stopThum()


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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


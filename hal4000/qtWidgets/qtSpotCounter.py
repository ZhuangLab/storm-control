#!/usr/bin/python
#
# Qt Thread for counting the number of spots 
# in a frame and graphing the results.
#
# Hazen 3/09
#

from PyQt4 import QtCore, QtGui

try:
    import objectFinder.fastObjectFinder as FOF
except:
    import sys
    sys.path.append("../")
    import objectFinder.fastObjectFinder as FOF


#
# The thread class, which does all the actual object counting.
#
class QObjectCounterThread(QtCore.QThread):
    def __init__(self, parameters, index, timing_mode = 0, parent = None):
        QtCore.QThread.__init__(self, parent)

        self.FOF = FOF.MedFastObjectFinder(parameters.cell_size,
                                           parameters.threshold)
        self.mutex = QtCore.QMutex()
        self.running = 1
        self.image_x = parameters.x_pixels/parameters.x_bin
        self.image_y = parameters.y_pixels/parameters.y_bin
        self.image = 0
        self.thread_index = index
        self.frame_index = 0
        self.counts = 0

        self.timing_mode = timing_mode
        self.x_locs = 0
        self.y_locs = 0
        self.spots = 0
        self.retrieved = 1

    def getCounts(self):
        self.mutex.lock()
        temp = self.counts
        self.mutex.unlock()
        return temp

    def getData(self):
        self.mutex.lock()
        x_locs = self.x_locs
        y_locs = self.y_locs
        spots = self.spots
        self.retrieved = 1
        self.mutex.unlock()
        return [x_locs, y_locs, spots]

    def newImage(self, image, index):
        self.mutex.lock()
        self.frame_index = index
        self.image = image
        self.mutex.unlock()

    def run(self):
         while (self.running):
            self.mutex.lock()
            if self.image and self.retrieved:
                [self.x_locs, self.y_locs, self.spots] = self.FOF.findObjects(self.image,
                                                                              self.image_x,
                                                                              self.image_y)
                if self.timing_mode:
                    self.counts += 1
                else:
                    self.retrieved = 0
                    self.emit(QtCore.SIGNAL("imageProcessed(int, int)"), 
                              self.thread_index, 
                              self.frame_index)
                    self.image = 0
            self.mutex.unlock()
            if not(self.timing_mode):
                self.usleep(50)

    def stopThread(self):
        self.running = 0


#
# The front end.
#
class QObjectCounter(QtGui.QWidget):
    def __init__(self, parameters, number_threads = 16, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.total = 0
        self.dropped = 0
        self.number_threads = number_threads
        self.frame_index = 0

        self.idle = []
        self.threads = []
        for i in range(self.number_threads):
            self.threads.append(QObjectCounterThread(parameters, i))
            self.idle.append(1)
            
        for thread in self.threads:
            thread.start(QtCore.QThread.NormalPriority)
            self.connect(thread, QtCore.SIGNAL("imageProcessed(int, int)"), self.imageProcessed)

    def getResults(self, thread_index):
        self.idle[thread_index] = 1
        return self.threads[thread_index].getData()

    def imageProcessed(self, thread_index, frame_index):
        self.emit(QtCore.SIGNAL("imageProcessed(int, int)"), thread_index, frame_index)

    def newImageToCount(self, image):
        self.total += 1
        if image:
            i = 0
            not_found = 1
            while (i < self.number_threads) and not_found:
                if self.idle[i]:
                    self.threads[i].newImage(image, self.frame_index)
                    self.idle[i] = 0
                    not_found = 0
                i += 1
            if not_found:
#            print "Spot counter dropped a frame."
                self.dropped += 1
        self.frame_index += 1

    def reset(self):
        self.frame_index = 0

    def shutDown(self):
        for thread in self.threads:
            thread.stopThread()
            thread.wait()
        print "Spot counter dropped", self.dropped, "images out of", self.total, "total images"


#
# Testing
#

if __name__ == "__main__":
    import ctypes
    import time

    class Parameters():
        def __init__(self):
            self.x_pixels = 512
            self.y_pixels = 512
            self.x_bin = 1
            self.y_bin = 1
            self.cell_size = 32
            self.threshold = 3.0
            self.coefficients = [-25, 0.05, 7.0e-6]

    parameters = Parameters()
    image_x = 512
    image_y = 512
    image_type = ctypes.c_short * (image_x * image_y)
    threads = []
    number_threads = 4
    for i in range(number_threads):
        threads.append(QObjectCounterThread(parameters, i, timing_mode = 1))
        image = image_type()
        threads[i].newImage(image, 1)

    for thread in threads:
        thread.start(QtCore.QThread.NormalPriority)

    wait_time = 5
    time.sleep(wait_time)
    sum = 0
    for thread in threads:
        thread.stopThread()

    for thread in threads:
        thread.wait()
        sum += thread.getCounts()

    print "Processed:", sum, "images in", wait_time, "seconds"
    print "%.3f" % (sum/wait_time), "images per second"
        

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


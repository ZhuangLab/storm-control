#!/usr/bin/python
#
# Qt Thread for counting the number of spots 
# in a frame and graphing the results.
#
# Hazen 12/12
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
    imageProcessed = QtCore.pyqtSignal(int, object, int, object, object, int)

    def __init__(self, index, timing_mode = 0, parent = None):
        QtCore.QThread.__init__(self, parent)

        self.FOF = FOF.MedFastObjectFinder(parameters.cell_size,
                                           parameters.threshold)

        self.frame = False
        self.mutex = QtCore.QMutex()
        self.running = 1
        self.thread_index = index

        self.counts = 0
        self.timing_mode = timing_mode

    def newImage(self, frame):
        self.mutex.lock()
        self.frame = frame
        self.mutex.unlock()

    def run(self):
         while (self.running):
            self.mutex.lock()
            if self.image:
                [x_locs, y_locs, spots] = self.FOF.findObjects(self.frame.data,
                                                               self.frame.image_x,
                                                               self.frame.image_y)
                if self.timing_mode:
                    self.counts += 1
                else:
                    self.imageProcessed.emit(self.thread_index,
                                             self.frame.which_camera,
                                             self.frame.number,
                                             x_locs,
                                             y_locs,
                                             spots)
            self.mutex.unlock()
            if not(self.timing_mode):
                self.usleep(50)

    def stopThread(self):
        self.running = 0


#
# The front end.
#
class QObjectCounter(QtGui.QWidget):
    imageProcessed = QtCore.pyqtSignal(object, int, object, object, int)

    def __init__(self, number_threads = 16, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.total = 0
        self.dropped = 0
        self.number_threads = number_threads

        self.idle = []
        self.threads = []
        for i in range(self.number_threads):
            self.threads.append(QObjectCounterThread(i))
            self.idle.append(True)
            
        for thread in self.threads:
            thread.start(QtCore.QThread.NormalPriority)
            thread.imageProcessed.connect(self.returnResults)

    def newImageToCount(self, frame):
        self.total += 1
        if image:
            i = 0
            not_found = True
            while (i < self.number_threads) and not_found:
                if self.idle[i]:
                    self.threads[i].newImage(frame)
                    self.idle[i] = False
                    not_found = False
                i += 1
            if not_found:
                self.dropped += 1

    def returnResults(self, thread_index, which_camera, frame_number, x_locs, y_locs, spots):
        self.idle[thread_index] = True
        self.imageProcessed.emit(which_camera,
                                 frame_number,
                                 x_locs,
                                 y_locs,
                                 spots)

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


#!/usr/bin/python
#
# Qt Thread for counting the number of spots 
# in a frame and graphing the results.
#
# Hazen 09/13
#

from PyQt4 import QtCore, QtGui

try:
    import objectFinder.lmmObjectFinder as lmmObjectFinder
except:
    import sys
    sys.path.append("../")
    import objectFinder.lmmObjectFinder as lmmObjectFinder


#
# The thread class, which does all the actual object counting.
#
class QObjectCounterThread(QtCore.QThread):
    imageProcessed = QtCore.pyqtSignal(int, object, int, object, object, int)

    def __init__(self, parameters, index, parent = None):
        QtCore.QThread.__init__(self, parent)

        self.frame = False
        self.mutex = QtCore.QMutex()
        self.running = True
        self.thread_index = index
        self.threshold = parameters.threshold

    def newImage(self, frame):
        self.mutex.lock()
        self.frame = frame
        self.mutex.unlock()

    def newParameters(self, parameters):
        self.mutex.lock()
        self.threshold = parameters.threshold
        self.mutex.unlock()

    def run(self):
         while (self.running):
             self.mutex.lock()
             if self.frame:
                 [x_locs, y_locs, spots] = lmmObjectFinder.findObjects(self.frame.data,
                                                                       self.frame.image_x,
                                                                       self.frame.image_y,
                                                                       self.threshold)
                 self.imageProcessed.emit(self.thread_index,
                                          self.frame.which_camera,
                                          self.frame.number,
                                          x_locs,
                                          y_locs,
                                          spots)
                 self.frame = False
                     
             self.mutex.unlock()
             self.usleep(50)

    def stopThread(self):
        self.running = False


#
# The front end.
#
class QObjectCounter(QtGui.QWidget):
    imageProcessed = QtCore.pyqtSignal(object, int, object, object, int)

    def __init__(self, parameters, number_threads = 16, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.dropped = 0
        self.number_threads = number_threads
        self.total = 0

        # Initialize object finder.
        lmmObjectFinder.initialize()

        # Initialize threads.
        self.idle = []
        self.threads = []
        for i in range(self.number_threads):
            self.threads.append(QObjectCounterThread(parameters, i))
            self.idle.append(True)
            
        for thread in self.threads:
            thread.start(QtCore.QThread.NormalPriority)
            thread.imageProcessed.connect(self.returnResults)

    def newImageToCount(self, frame):
        self.total += 1
        if frame:
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

    def newParameters(self, parameters):
        for thread in self.threads:
            thread.newParameters(parameters)

    def returnResults(self, thread_index, which_camera, frame_number, x_locs, y_locs, spots):
        self.idle[thread_index] = True
        self.imageProcessed.emit(which_camera,
                                 frame_number,
                                 x_locs,
                                 y_locs,
                                 spots)

    def shutDown(self):
        # Object finder cleanup.
        lmmObjectFinder.cleanup()

        # Thread cleanup.
        for thread in self.threads:
            thread.stopThread()
            thread.wait()
        print "Spot counter dropped", self.dropped, "images out of", self.total, "total images"


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


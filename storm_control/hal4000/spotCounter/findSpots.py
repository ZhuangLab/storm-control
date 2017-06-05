#!/usr/bin/env python
"""
Analyze frames using QRunnables and QThreadPool.

Hazen 05/17
"""

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.spotCounter.lmmObjectFinder as lmmObjectFinder


class AnalysisWorker(QtCore.QRunnable):
    """
    Runnable for performing image analysis.
    """
    def __init__(self, frame_analysis = None, **kwds):
        super().__init__(**kwds)
        self.frame_analysis = frame_analysis

    def run(self):
        self.frame_analysis.analyzeImage()

    
class FrameAnalysis(QtCore.QObject):
    """
    This class:
     1. Stores the frame to analyze.
     2. Does the analysis (with AnalysisWorker).
     3. Stores the results of the analysis.
     4. Signals when the analysis is done.
    """
    analysisDone = QtCore.pyqtSignal(object)
    
    def __init__(self,
                 camera_name = None,
                 frame = None,
                 threshold = None,
                 **kwds):
        super().__init__(**kwds)
        self.camera_name = camera_name
        self.frame = frame
        self.locs_count = 0
        self.threshold = threshold
        self.x_locs = None
        self.y_locs = None

    def analyzeImage(self):
        [self.x_locs, self.y_locs, self.locs_count] = lmmObjectFinder.findObjects(self.frame,
                                                                                  self.threshold)
        self.analysisDone.emit(self)

    def getCameraName(self):
        return self.camera_name
    
    def getCounts(self):
        return self.locs_count

    def getFrameNumber(self):
        return self.frame.frame_number
        
    def getLocalizations(self):
        return [self.x_locs[:self.locs_count],
                self.y_locs[:self.locs_count]]
        

class SpotCounter(QtCore.QObject):
    imageProcessed = QtCore.pyqtSignal(object)

    def __init__(self, free_threads = None, **kwds):
        super().__init__(**kwds)

        self.dropped = 0
        self.in_process = []
        self.threadpool = halModule.threadpool
        self.total = 0

        #
        # Leave at least free_threads free for other HAL modules to use.
        #
        self.max_thread_count = self.threadpool.maxThreadCount() - free_threads

        # Initialize object finder.
        lmmObjectFinder.initialize()

    def cleanUp(self):
        
        # Object finder cleanup.
        lmmObjectFinder.cleanup()

        # Print statistics.
        print("Spot counter dropped", self.dropped, "images out of", self.total, "total images")

    def handleAnalysisDone(self, frame_analysis):
        self.in_process.remove(frame_analysis)
        frame_analysis.analysisDone.disconnect(self.handleAnalysisDone)
        self.imageProcessed.emit(frame_analysis)
        
    def newFrameToAnalyze(self, camera_name, frame, threshold):
        self.total += 1

        # Check if there is a thread available to analyze the image.
        if (self.threadpool.activeThreadCount() < self.max_thread_count):

            # Create analysis object.
            frame_analysis = FrameAnalysis(camera_name = camera_name,
                                           frame = frame,
                                           threshold = threshold)
            frame_analysis.analysisDone.connect(self.handleAnalysisDone)
            self.in_process.append(frame_analysis)

            # Start analysis.
            self.threadpool.start(AnalysisWorker(frame_analysis = frame_analysis))

        else:
            self.dropped += 1
            
#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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


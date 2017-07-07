#!/usr/bin/env python
"""
Analyze frames using QRunnables and QThreadPool.

Hazen 05/17
"""
import time

from PyQt5 import QtCore

import storm_control.hal4000.halLib.halModule as halModule
import storm_control.hal4000.spotCounter.lmmObjectFinder as lmmObjectFinder


class AnalysisWorker(QtCore.QRunnable):
    """
    Runnable for performing image analysis.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.aw_signaler = AnalysisWorkerSignaler()
        self.frame_analysis = None
        self.busy = False

    def isBusy(self):
        return self.busy
        
    def run(self):
        self.frame_analysis.analyzeImage()
        self.aw_signaler.analysisDone.emit(self.frame_analysis)
        self.busy = False
        
    def setFrameAnalysis(self, frame_analysis):
        self.frame_analysis = frame_analysis
        self.busy = True


class AnalysisWorkerSignaler(QtCore.QObject):
    """
    Signal class used by the AnalysisWorker to indicate that
    the analysis of a frame is complete.
    """
    analysisDone = QtCore.pyqtSignal(object)

    
class FrameAnalysis(QtCore.QObject):
    """
    This class:
     1. Stores the frame to analyze.
     2. Does the analysis (with AnalysisWorker).
     3. Stores the results of the analysis.
    """
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

    def __init__(self, max_threads = None, max_size = 0, **kwds):
        super().__init__(**kwds)

        self.dropped = 0
        self.max_size = max_size
        self.threadpool = halModule.threadpool
        self.total = 0
        self.workers = []

        # Create analysis workers.
        for i in range(max_threads):
            aw = AnalysisWorker()
            aw.setAutoDelete(False)
            aw.aw_signaler.analysisDone.connect(self.handleAnalysisDone)
            self.workers.append(aw)

        # Initialize object finder.
        lmmObjectFinder.initialize()
            
    def cleanUp(self):

        # Wait for workers to finish.
        still_busy = True
        while still_busy:
            all_busy = False
            for worker in self.workers:
                if worker.isBusy():
                    all_busy = True
                    break
            still_busy = all_busy
            time.sleep(0.1)
        
        # Object finder cleanup.
        lmmObjectFinder.cleanUp()

        # Print statistics.
        print("> spot counter dropped", self.dropped, "images out of", self.total, "total images")

    def handleAnalysisDone(self, frame_analysis):
        self.imageProcessed.emit(frame_analysis)
        
    def newFrameToAnalyze(self, camera_name, frame, threshold):
        
        # Check if the current camera image is small
        # enough that we can analyze it.
        if ((frame.image_x * frame.image_y) > self.max_size):
            return
        
        self.total += 1

        # Check if there is a thread available to analyze the image.
        was_dropped = True
        for worker in self.workers:
            if not worker.isBusy():
                worker.setFrameAnalysis(FrameAnalysis(camera_name = camera_name,
                                                      frame = frame,
                                                      threshold = threshold))
                self.threadpool.start(worker)
                was_dropped = False
                break

        if was_dropped:
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


#!/usr/bin/env python
"""
A test of the BufferedFunctionality class.
"""
import sys
import time

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class BufferedTest(hardwareModule.BufferedFunctionality):
    processed = QtCore.pyqtSignal(str)
    
    def processRequest(self, request):
        time.sleep(0.2)
        self.processed.emit(request)

class TBWidget(QtWidgets.QWidget):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.strings = []
        self.tb = BufferedTest()
        self.timer = QtCore.QTimer()

        self.timer.setInterval(10)
        self.timer.timeout.connect(self.runTest)
        self.timer.setSingleShot(True)
        self.timer.start()

        self.tb.processed.connect(self.handleProcessed)

    def handleProcessed(self, string):
        self.strings.append(string)
        if (string == "end"):
            assert(self.strings == ["111", "212", "end"])
            self.close()
        
    def runTest(self):
        strings = ["111", "222", "333", "444", "555", "end"]
        for string in strings:
            self.tb.maybeProcess(string)
            if(string == "222"):
                self.tb.mustProcess("212")

def test_buffered():
    app = QtWidgets.QApplication(sys.argv)
    tb1 = TBWidget()
    app.exec_()
    
if (__name__ == "__main__"):
    test_buffered()

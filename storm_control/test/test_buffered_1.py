#!/usr/bin/env python
"""
A test of the BufferedFunctionality class.
"""
import sys
import time

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class TBWidget(QtWidgets.QWidget):
    processed = QtCore.pyqtSignal(str)
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.bf = hardwareModule.BufferedFunctionality()
        self.strings = []
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.runTest)
        self.timer.setSingleShot(True)
        self.timer.start()

        self.processed.connect(self.handleProcessed)

    def editString(self, string):
        time.sleep(0.2)
        string = "0" + string
        return string
    
    def handleProcessed(self, string):
        self.strings.append(string)
        if "end" in string:
            try:
                assert(self.strings == ["0111", "0212", "0end"])
            except AssertionError as exc:
                print(self.strings, "is not expected")
                raise exc
            self.bf.wait()
            self.close()
        
    def runTest(self):
        for string in ["111", "222", "333", "444", "555", "end"]:
            self.bf.maybeRun(task = self.editString,
                             args = [string],
                             ret_signal = self.processed)
            if(string == "222"):
                self.bf.mustRun(task = self.editString,
                                args = ["212"],
                                ret_signal = self.processed)

def test_buffered():
    app = QtWidgets.QApplication(sys.argv)
    tb1 = TBWidget()
    app.exec_()
    app = None
    
if (__name__ == "__main__"):
    test_buffered()

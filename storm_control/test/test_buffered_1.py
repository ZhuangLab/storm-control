#!/usr/bin/env python
"""
A test of the BufferedFunctionality class.
"""
import sys
import time

from PyQt5 import QtCore, QtWidgets

import storm_control.sc_hardware.baseClasses.hardwareModule as hardwareModule


class TBWidgetBase(QtWidgets.QWidget):
    processed = QtCore.pyqtSignal(str)
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.bf = hardwareModule.BufferedFunctionality(device_mutex = QtCore.QMutex())
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.runTest)
        self.timer.setSingleShot(True)
        self.timer.start()

        self.processed.connect(self.handleProcessed)

    def handleProcessed(self, string):
        pass

    def runTest(self):
        pass
    
            
class TBWidget1(TBWidgetBase):
    """
    Check for correct execution order.
    """    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.strings = []

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


class TBWidget2(TBWidgetBase):
    """
    Check that kill timer works.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.bf.kill_timer.setInterval(200)

    def handleProcessed(self, string):
        assert False
        
    def longWait(self):
        time.sleep(2.0)

    def runTest(self):
        self.bf.mustRun(task = self.longWait,
                        args = [],
                        ret_signal = self.processed)


class TBWidget3(TBWidgetBase):
    """
    Check that kill timer reset works.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.max_jobs = 20
        self.bf.kill_timer.setInterval(500)

    def handleProcessed(self, string):
        print("processed", string)
        if (string == str(self.max_jobs - 1)):
            self.bf.wait()
            self.close()
        
    def shortWait(self, job_id):
        time.sleep(0.1)
        return job_id

    def runTest(self):
        for i in range(self.max_jobs):
            self.bf.mustRun(task = self.shortWait,
                            args = [str(i)],
                            ret_signal = self.processed)        
                

def test_buffered_1():
    app = QtWidgets.QApplication(sys.argv)
    tb1 = TBWidget1()
    app.exec_()
    app = None

def buffered_2():
    app = QtWidgets.QApplication(sys.argv)
    tb1 = TBWidget2()
    app.exec_()
    app = None

def test_buffered_3():
    app = QtWidgets.QApplication(sys.argv)
    tb1 = TBWidget3()
    app.exec_()
    app = None    
    
if (__name__ == "__main__"):
    test_buffered_1()
    #buffered_2()
    test_buffered_3()

#!/usr/bin/env python
"""
This is a test for travis-ci to help figure out why all of
our tests that involve PyQt5 abort.
"""

import sys
from PyQt5 import QtCore,QtWidgets

class HelloWidget(QtWidgets.QWidget):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.setMinimumSize(QtCore.QSize(640, 480))    
        self.setWindowTitle("Hello world")

        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.close)
        self.timer.start()
        

def test_hello_world():
    app = QtWidgets.QApplication(sys.argv)
    hw = HelloWidget()
    hw.show()
    app.exec_()
    app = None

#!/usr/bin/python
#
## @file
#
# The default miscControl class.
#
# Hazen 06/12
#

import sys
from PyQt4 import QtCore, QtGui

import qtWidgets.qtAppIcon as qtAppIcon

# Debugging
import halLib.hdebug as hdebug

## MiscControl
#
# Misc Control Dialog Box
#
class MiscControl(QtGui.QDialog):

    ## __init__
    #
    # @param parameters A parameters object.
    # @param tcp_control A TCP control object.
    # @param camera_widget A camera (display area) widget.
    # @param parent (Optional) The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, parameters, tcp_control, camera_widget, parent = None):
        QtGui.QDialog.__init__(self, parent)
        
        self.camera_widget = camera_widget
        self.parameters = parameters
        self.tcp_control = tcp_control

        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        self.setWindowIcon(qtAppIcon.QAppIcon())

    ## closeEvent
    #
    # Close the window if it does not have a parent, otherwise just hide it.
    #
    # @param event A PyQt event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    ## handleQuit
    #
    # Close the window.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        self.close()

    ## newFrame
    #
    # Called when there is new data from the camera during film acquisition.
    #
    @hdebug.debug
    def newFrame(self, frame):
        pass

    ## quit
    #
    # Cleans up when the progam exits.
    #
    @hdebug.debug
    def quit(self):
        pass

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

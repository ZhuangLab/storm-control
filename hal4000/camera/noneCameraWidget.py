#!/usr/bin/python
#
# qtCameraWidget speciliazed for data for no camera.
#
# Hazen 11/09
#

from PyQt4 import QtCore

import qtWidgets.qtCameraWidget as qtCameraWidget

try:
    import andor.formatconverters as fconv
except:
    print "failed to load andor.formatconverters."

# None Camera widget
class ACameraWidget(qtCameraWidget.QCameraWidget):
    def __init__(self, parent = None):
        qtCameraWidget.QCameraWidget.__init__(self, parent)

    def updateImageWithData(self, new_data):
        if new_data:
            # update image
            w = self.image.width()
            h = self.image.height()
            [self.image_min, self.image_max] = fconv.andorToQtImage(new_data,
                                                                    int(self.image.scanLine(0)),
                                                                    w * h,
                                                                    self.display_range[0], self.display_range[1])
            self.update()
            # emit signal with camera intensity information at last click location
            if self.show_info:
                x_loc = (self.x * w)/512
                y_loc = (self.y * h)/512
                loc = 2*(y_loc * w + x_loc)
                # FIXME: range check needed.
                value = ord(new_data[loc]) + 255*ord(new_data[loc+1])
                self.emit(QtCore.SIGNAL("intensityInfo(int, int, int)"), x_loc, y_loc, value)

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

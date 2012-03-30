#!/usr/bin/python
#
# LDC210 diode laser driver on/off control
#
# Hazen 9/09
#

import sys
import time

try:
    import nationalInstruments.nicontrol as nicontrol
except:
    sys.path.append("..")
    import nationalInstruments.nicontrol as nicontrol

class LDC210():
    def __init__(self, board, line):
        self.board = board
        self.line = line
        
    def on(self):
        nicontrol.setDigitalLine(self.board, self.line, True)

    def off(self):
        nicontrol.setDigitalLine(self.board, self.line, False)


if __name__ == "__main__":
    ldc = LDC210("PCI-6733", 7)
    ldc.on()
    time.sleep(1)
    ldc.off()

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

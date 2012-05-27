#!/usr/bin/python
#
# Dummy classes for use when you have some but not all 
# of the focus lock functionality.
#
# Hazen 12/09
#

# Fake QPD
class QPD():
    def __init__(self):
        pass

    def qpdScan(self):
        return [1000.0, 0.0, 0.0]

    def shutDown(self):
        pass

# Fake nano-positioner
class NanoP():
    def __init__(self):
        pass

    def zMoveTo(self, position):
        pass

    def shutDown(self):
        pass

# Fake IR laser
class IRLaser():
    def __init__(self):
        pass

    def havePowerControl(self):
        return False

    def on(self):
        pass

    def off(self):
        pass
    
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

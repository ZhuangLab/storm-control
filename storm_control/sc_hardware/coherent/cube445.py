#!/usr/bin/python
#
## @file
#
# Coherent CUBE 445 laser control.
#
# Hazen 7/10
#

import cube

## Cube445
#
# Controls a Coherent Cube 445 laser. This is sub-class of cube.Cube.
#
class Cube445(cube.Cube):

    ## __init__
    #
    # Initiate RS-232 communication, verify that the laser is responding.
    #
    # @param port (Optional) A string that specifies the port, the default is "COM1".
    #
    def __init__(self, port = "COM1"):
        cube.Cube.__init__(self, port)

#
# Testing
#

if __name__ == "__main__":
    cube = Cube445()
    if cube.getStatus():
        print cube.getPowerRange()
        print cube.getLaserOnOff()

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


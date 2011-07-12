#!/usr/bin/python
#
# Debugging decorator.
#
# Hazen 02/10
#

want_debugging = False

def debug(fn):
    def debug_f(*args, **kw):
        if fn.__module__ == "__main__":
            print fn.__module__ + "." + fn.__name__ + ":"
            for i, arg in enumerate(args):
                print "    " + str(i) + ".", arg
        else:
            print "  " + fn.__module__ + "." + fn.__name__ + ":"
            for i, arg in enumerate(args):
                print "      " + str(i) + ".", arg
        return fn(*args, **kw)
    global want_debugging
    if want_debugging:
        return debug_f
    else:
        return fn

def getDebug():
    return want_debugging

# Needs to be set at compile time?
def setDebugging(state):
    global want_debugging
    if state:
        want_debugging = True
    else:
        want_debugging = False


#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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

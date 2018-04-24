#!/usr/bin/env python
"""
A very simple git parser. Note that this will only give the 
correct answer if you run it in a storm-control directory.

Hazen 02/18
"""
import subprocess
from subprocess import check_output

branch = "master"
version = ""
try:
    branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip().decode()
    version = check_output(["git", "rev-parse", "HEAD"]).strip().decode()
except FileNotFoundError:
    pass
except subprocess.CalledProcessError:
    pass
    
def getBranch():
    return branch

def getVersion():
    return version

if (__name__ == "__main__"):
    print("Branch:", branch)
    print("Version:", version)

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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

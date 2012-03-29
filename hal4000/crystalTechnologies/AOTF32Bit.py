#!/usr/bin/python
#
# This is part of the work-around for the lack
# of a 64 bit version of the AotfLibrary.dll file.
#
# Hazen 3/12
#

import sys

import AOTF

my_aotf = AOTF.AOTF()

while True:
   next_cmd = sys.stdin.readline()
   if not next_cmd:
      break
   next_cmd = next_cmd[:-1] if next_cmd.endswith('\n') else next_cmd
   response = my_aotf._sendCmd(next_cmd)
   if (not response) or ("Invalid" in response):
      sys.stdout.write("failed\n")
   else:
      sys.stdout.write(next_cmd + "\n")
   sys.stdout.flush()

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
 

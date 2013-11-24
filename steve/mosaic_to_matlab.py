#!/usr/bin/python
#
## @file
#
# Convert .stv files to .mat files for those who persist in using Matlab
# and want to be able to manipulate image mosaics.
#
# Hazen 07/13
#

import os
import pickle
import numpy
import scipy.io
import sys

if (len(sys.argv) != 2):
    print "Usage <mosaic_file>"
    exit()

directory = os.path.dirname(sys.argv[1])
if (len(directory) == 0):
    directory = "."

fp = open(sys.argv[1], "r")

file_number = 1
while 1:
    line = fp.readline().rstrip()
    if not line: break

    data = line.split(",")
    if (data[0] == "image"):
        image_name = data[1]

        print "converting:", image_name

        image_dict = pickle.load(open(directory + "/" + image_name))

        mat_dict = {}
        for key in image_dict:
            val_type = type(image_dict[key])
            #print key, val_type
            if (val_type in [type(""), type(0), type(0.0), type(numpy.array([]))]):
            #print key, type(image_dict[key])
                mat_dict[key] = image_dict[key]
            else:
            #print key, str(image_dict[key])
                mat_dict[key] = str(image_dict[key])

        scipy.io.savemat(directory + "/" + image_name[:-4] + ".mat", mat_dict)
        
        file_number += 1

fp.close()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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

#!/usr/bin/python
#
## @file
#
# Python interface to the format_converter library.
#
# Hazen 2/09
#

from ctypes import *
import os

formatconverter = 0

## loadFormatConverterDLL
#
# Loads the C format converter DLL, but only once.
#
def loadFormatConverterDLL():
    global formatconverter
    if formatconverter == 0:
        if os.path.exists("format_converters.dll"):
            formatconverter = cdll.LoadLibrary("format_converters")
        else:
            formatconverter = cdll.LoadLibrary("andor/format_converters")

loadFormatConverterDLL()

## andorToQtImage
#
# Copies the image data from the AndorCamera class image buffer into
# a 8bit qt_image buffer, rescaling the data as requested. This returns
# the minimum and maximum value in the image as a side effect.
#
# In the process of changing setting (going from 512x512 to 256x256 say)
# we'll often end up in here with some frames that are the wrong size.
# Usually this is not a problem, so we just print a warning and continue
# as if we weren't struggling to deal with multi-threaded code.
#
# @param andor_data This is a ctypes string buffer.
# @param qt_image_data_sip_ptr This a pointer to where the QImage will store its data.
# @param qt_image_size The size of the QImage (total number of pixels).
# @param min The value in andor_data that will be 0 in the QImage.
# @param max Tha value in andor_data that will be 255 in the QImage.
#
def andorToQtImage(andor_data, qt_image_data_sip_ptr, qt_image_size, min, max):
    image_min = c_int(4096)
    image_max = c_int(0)
    andor_data_len = len(andor_data)/2
#    assert qt_image_size == andor_data_len, "andorToQtImage: buffers must be the same size! " + str(andor_data_len) + " " + str(qt_image_size)
    if qt_image_size == andor_data_len:
        formatconverter.andorToQtImage(andor_data, qt_image_data_sip_ptr, andor_data_len, c_int(min), c_int(max), byref(image_min), byref(image_max))
    else:
        print "andorToQtImage: buffers are not the same size! " + str(andor_data_len) + " " + str(qt_image_size)
    return [image_min.value, image_max.value]


## LEtoBE
#
# Converts from little to big endian.
#
# @param le_data ctypes string buffer containing the (16 bit) image data.
#
def LEtoBE(le_data):
    le_data_len = len(le_data)
    be_data = create_string_buffer(le_data_len)
    formatconverter.andorToBigEndian(le_data, be_data, le_data_len)
    return be_data


#
# Testing
# 

if __name__ == "__main__":

    min = 200
    max = 300
    range = max - min
    char1 = chr(10)
    char2 = chr(1)
    andor_data = create_string_buffer(2)
    andor_data.raw = char1 + char2
    qt_data = c_char('c')

    print "1", repr(andor_data.raw), qt_data
    formatconverter.andorToQtImage(andor_data, byref(qt_data), 1, min, max)

    correct = ord(char1) + ord(char2) * 256
    print correct
    correct = (correct - min)*256/range

    if correct < 0:
        correct = 0
    if correct > 255:
        correct = 255
    print "2", repr(andor_data.raw), ord(qt_data.value), "=", correct


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


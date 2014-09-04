#!/usr/bin/python
#
## @file
#
# Conversion of XML node(s) to dictionaries.
#
# Hazen 09/14
#


## getField
#
# Return the value of a field, or default_value if the field does not exist.
#
# @param node A ElementTree xml node.
# @param field The name of the field (or None).
# @param convert_fn The function to use for conversion, or None if no conversion is desired.
# @param default (Optional) The value to return if the field is not found.
#
# @return The field converted with convert_fn or default_value if the field is not found.
#
def gf(convert_fn, default_value = None):
    def getField(node, field):
        temp = node.find(field)
        if temp is not None:
            if convert_fn is not None:
                return convert_fn(temp.text)
            else:
                return temp
        else:
            return default_value
    return getField

movie_node_conversion = {"delay" : gf(int, 0),
                         "directory" : gf(str),
                         "length" : gf(int),
                         "name" : gf(str),
                         "min_spots" : gf(int),
                         "overwrite" : gf(bool),
                         "parameters" : gf(str)}

## movieNodeToDict
#
# Convert a xml movie to a dictionary.
#
# @param movie_node The xml of a movie node.
#
# @return A dictionary describing the movie node.
#
def movieNodeToDict(movie_node):
    dict = {}
    for field in movie_node_conversion.keys():
        value = movie_node_conversion[field](movie_node, field)
        if value is not None:
            dict[field] = value
    return dict

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

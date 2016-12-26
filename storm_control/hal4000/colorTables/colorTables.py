#!/usr/bin/python
#
## @file
#
# Handles the color tables.
#
# Hazen 3/09
#

import os


## getColorTables
#
# Returns all the color tables available in a directory.
# 
# Based on:
#  http://codecomments.wordpress.com/2008/07/10/find-files-in-directory-using-python/
#
# @param directory The directory to search for color tables.
#
def getColorTables(directory):
    fileList = os.listdir(directory)
    return [f for f in fileList if f.find(".ctbl") > -1]

## ColorTables
#
# This class encapsulates color table handling.
#
class ColorTables(object):

    ## __init__
    #
    # Create a color table handling object. This searches the
    # specficied directory for .ctbl files. It the loads the
    # first file that it finds as the starting color table.
    #
    # @param directory The directory containing the color tables.
    #
    def __init__(self, directory):
        self.directory = directory
        self.table_names = getColorTables(directory)
        self.table_name = self.table_names[0]
        self.index = 0
        self.table = []
        self.loadColorTable()

    ## currentTable
    #
    # @return [the color table, the color table's name]
    #
    def currentTable(self):
        return [self.table, self.table_name]

    ## getColorTableNames
    #
    # @return The names of all the color tables.
    #
    def getColorTableNames(self):
        return self.table_names

    ## getNextTable
    #
    # Returns the next table in the list after the current color table.
    #
    # @return [the color table, the color table's name]
    #
    def getNextTable(self):
        self.index += 1
        if self.index >= len(self.table_names):
            self.index = 0
        self.table_name = self.table_names[self.index]
        self.loadColorTable()
        return [self.table, self.table_name]

    ## getTableByName
    #
    # Returns the color table with the specified name, or the current
    # color table if it can't find the requested color table.
    #
    # @param name The name of the color table to load.
    #
    # @return [the color table, the color table's name]
    #
    def getTableByName(self, name):
        index = -1
        try:
            index = self.table_names.index(name)
        except:
            print(" ", name, "not found")
        if not index == -1:
            self.index = index
            self.table_name = self.table_names[self.index]
            self.loadColorTable()
        return self.table

    ## loadColorTable
    #
    # Load a color table from a .ctbl file. This loads the color table
    # specified in self.table_name.
    #
    def loadColorTable(self):
        self.table = []
        ctbl_file = open(self.directory + self.table_name, "r")
        while 1:
            line = ctbl_file.readline()
            if not line: break
            line = line[:-2]
            [r, g, b] = line.split(" ")
            self.table.append([int(r), int(g), int(b)])


#
# Testing
# 

if (__name__ == "__main__"):
    test = ColorTables("./all_tables/")
    [table, name] = test.currentTable()
    print(name)
    [table, name] = test.getTableByName("idl5.ctbl")
    print(name)


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


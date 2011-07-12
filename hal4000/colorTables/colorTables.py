#!/usr/bin/python
#
# Handles the color tables.
#
# Hazen 3/09
#

import os


# Returns all the color tables available in a directory.
# 
# Based on:
#  http://codecomments.wordpress.com/2008/07/10/find-files-in-directory-using-python/
#
def getColorTables(directory):
    fileList = os.listdir(directory)
    return [f for f in fileList if f.find(".ctbl") > -1]

class ColorTables:
    def __init__(self, directory):
        self.directory = directory
        self.table_names = getColorTables(directory)
        self.table_name = self.table_names[0]
        self.index = 0
        self.table = []
        self.loadColorTable()

    def currentTable(self):
        return [self.table, self.table_name]

    def getColorTableNames(self):
        return self.table_names

    def getNextTable(self):
        self.index += 1
        if self.index >= len(self.table_names):
            self.index = 0
        self.table_name = self.table_names[self.index]
        self.loadColorTable()
        return [self.table, self.table_name]

    def getTableByName(self, name):
        index = -1
        try:
            index = self.table_names.index(name)
        except:
            print " ", name, "not found"
        if not index == -1:
            self.index = index
            self.table_name = self.table_names[self.index]
            self.loadColorTable()
        return self.table

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

if __name__ == "__main__":
    test = ColorTables("./all_tables/")
    [table, name] = test.currentTable()
    print name
    [table, name] = test.getTableByName("idl5.ctbl")
    print name


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


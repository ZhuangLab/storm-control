#!/usr/bin/python
#
## @file
#
# Handles parsing sequence xml files and generating movie objects.
#
# Hazen 12/10
#

from xml.dom import minidom, Node

import sc_library.hdebug as hdebug

## parseText
#
# Parses text using the functions specified by func.
#
# @param text The text to parse.
# @param func The function to parse the text with.
#
def parseText(text, func):
    if (len(text) > 0):
        return func(text)
    else:
        return None

## Progression
#
# The progression object.
#
class Progression:

    ## __init__
    #
    # Creates a progression object from the progression XML.
    #
    # @param progression_xml A xml node describing the progression.
    #
    def __init__(self, progression_xml):
        self.channels = []
        self.type = "none"

        if progression_xml:
            for node in progression_xml.childNodes:
                if node.nodeType == Node.ELEMENT_NODE:
                    if node.nodeName == "type":
                        self.type = node.firstChild.nodeValue
                    elif node.nodeName == "channel":
                        channel = int(node.firstChild.nodeValue)
                        start = parseText(node.getAttribute("start"), float)
                        frames = parseText(node.getAttribute("frames"), int)
                        inc = parseText(node.getAttribute("inc"), float)
                        self.channels.append([channel, start, frames, inc])
                    elif node.nodeName == "filename":
                        self.filename = node.firstChild.nodeValue


## Movie
#
# The movie object.
#
class Movie:

    ## __init__
    #
    # Dynamically create the class by processing the movie xml object.
    #
    # @param movie_xml A xml node describing the movie.
    #
    def __init__(self, movie_xml):

        # default settings
        self.delay = 0
        self.find_sum = 0.0
        self.length = 1
        self.min_spots = 0
        self.name = "default"
        self.pause = 1
        self.progression = None
        self.recenter = 0

        # parse settings
        for node in movie_xml.childNodes:
            if node.nodeType == Node.ELEMENT_NODE:
                if (node.nodeName == "delay"):
                    self.delay = int(node.firstChild.nodeValue)
                elif (node.nodeName == "find_sum"):
                    self.find_sum = float(node.firstChild.nodeValue)
                elif (node.nodeName == "length"):
                    self.length = int(node.firstChild.nodeValue)
                elif (node.nodeName == "lock_target"):
                    self.lock_target = float(node.firstChild.nodeValue)
                elif (node.nodeName == "min_spots"):
                    self.min_spots = int(node.firstChild.nodeValue)
                elif (node.nodeName == "name"):
                    self.name = node.firstChild.nodeValue
                elif (node.nodeName == "parameters"):
                    self.parameters = int(node.firstChild.nodeValue)
                elif (node.nodeName == "pause"):
                    self.pause = int(node.firstChild.nodeValue)
                elif (node.nodeName == "recenter"):
                    self.recenter = int(node.firstChild.nodeValue)
                elif (node.nodeName == "stage_x"):
                    self.stage_x = float(node.firstChild.nodeValue)
                elif (node.nodeName == "stage_y"):
                    self.stage_y = float(node.firstChild.nodeValue)

        # parse progressions
        progression_xml = movie_xml.getElementsByTagName("progression")
        if (len(progression_xml) > 0):
            self.progression = Progression(progression_xml[0])
        else:
            self.progression = Progression(None)

    ## __repr__
    #
    def __repr__(self):
        return hdebug.objectToString(self, "sequenceParser.Movie", ["name", "length", "stage_x", "stage_y"])

## parseMovieXml
#
# Parses the XML file that describes the movies.
#
# @param movie_xml_filename The name of the XML file.
#
def parseMovieXml(movie_xml_filename):
    xml = minidom.parse(movie_xml_filename)
    sequence = xml.getElementsByTagName("sequence").item(0)
    movies_xml = sequence.getElementsByTagName("movie")
    movies = []
    for movie_xml in movies_xml:
        movies.append(Movie(movie_xml))

    return movies


#
# Testing
# 

if __name__ == "__main__":
    print parseMovieXml("sequence.xml")



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

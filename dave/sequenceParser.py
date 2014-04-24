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

## AbstractCommand
#
# The base class for dave commands
#
class AbstractCommand():

    ## __init__
    #
    # Create default values
    #
    def __init__(self):
        self.name = "None"
        self.type = "None"

    ## getName
    #
    # Return the name of the command
    #
    def getName(self):
        return self.name

    ## getType
    #
    # Return the type of the command
    #
    def getType(self):
        return self.type

    ## getDescriptor
    #
    # Return a string that describes the command
    #
    def getDescriptor(self):
        return self.name + ": " + self.type

    ## getDetails
    #
    # Return a a list with details for display in a descriptor table
    #
    def getDetails(self):
        return [ [self.type, ""],
                 ["Name", self.name] ] 

## Movie
#
# The movie object.
#
class Movie(AbstractCommand):

    ## __init__
    #
    # Dynamically create the class by processing the movie xml object.
    #
    # @param movie_xml A xml node describing the movie.
    #
    def __init__(self, movie_xml):
        AbstractCommand.__init__(self)
        
        # Node type
        self.type = "movie"

        # default settings
        self.delay = 0
        self.find_sum = 0.0
        self.length = 0
        self.min_spots = 0
        self.name = "default"
        self.pause = False
        self.progression = None
        self.recenter = 0
        
        # parse settings
        for node in movie_xml.childNodes:
            if node.nodeType == Node.ELEMENT_NODE:
                if (node.nodeName == "directory"):
                    self.directory = node.firstChild.nodeValue
                elif (node.nodeName == "delay"):
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
                elif (node.nodeName == "overwrite"):
                    if node.firstChild.nodeValue == "True":
                        self.overwrite = True
                    else:
                        self.overwrite = False
                elif (node.nodeName == "parameters"):
                    try:
                        self.parameters = int(node.firstChild.nodeValue)
                    except:
                        self.parameters = str(node.firstChild.nodeValue)
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

    ## getDescriptor
    #
    # Return a string that describes the command
    #
    def getDescriptor(self):
        if hasattr(self, "stage_x") and hasattr(self, "stage_y"):
            return self.name + " ({0:.1f}, {1:.1f})".format(self.stage_x, self.stage_y)
        else:
            return self.name + " (Curr. Pos.)"

    ## getDetails
    #
    # Return a a list with details for display in a descriptor table
    #
    def getDetails(self):
        details = []
        # Movie header and name
        details.append(["Movie Command", ""])
        details.append(["Name", self.name])

        # Parameters
        if hasattr(self, "parameters"):
            details.append(["Parameters", str(self.parameters)])
        else:
            details.append(["Parameters", "None"])

        # Length
        details.append(["Frames", "{0:d}".format(self.length)])

        # Position
        if hasattr(self, "stage_x") and hasattr(self, "stage_y"):
            details.append(["Position", "({0:.2f}, {1:.2f})".format(self.stage_x, self.stage_y)])
        else:
            details.append(["Position", "Current"])

        # Delay
        details.append(["Delay", "{0:d}".format(self.delay)])

        # Sum
        if self.find_sum > 0.0:
            details.append(["Sum Target", "{0:.1f}".format(self.find_sum)])
        else:
            details.append(["Sum Target", "None"]);

        # Lock Target
        if hasattr(self, "lock_target"):
            details.append(["Lock Target", "{0:.1f}".format(self.lock_target)])
        else:
            details.append(["Lock Target", "None"])

        # Min Spots
        details.append(["Min Spots", "{0:d}".format(self.min_spots)])

        # Pause
        if self.pause:
            details.append(["Pause", "Yes"])
        else:
            details.append(["Pause", "No"])

        # Progression
        if hasattr(self.progression, "type"):
            display_str = self.progression.type
            if self.progression.type == "file":
                display_str += ": " + self.progression.filename
            details.append(["Progression", display_str])
        else:
            details.append(["Progression", "None"])

        # Recenter
        if self.recenter:
            details.append(["Recenter", "Yes"])
        else:
            details.append(["Recenter", "No"])

        return details
        
    ## __repr__
    #
    def __repr__(self):
        return hdebug.objectToString(self, "sequenceParser.Movie", ["name", "length", "stage_x", "stage_y"])

## ValveProtocol
#
# The fluidics protocol object.  This class controls communication with a valve chain
#
class ValveProtocol(AbstractCommand):
    ## __init__
    #
    # Dynamically create the class by processing the fluidics xml object.
    #
    # @param fluidics_xml A xml node describing the fluidics command.
    #
    def __init__(self, fluidics_xml):
        AbstractCommand.__init__(self)
        
        # node type
        self.type = "fluidics"
        
        # default settings
        self.protocol_name = []
        
        # passed single node
        node = fluidics_xml
        
        # parse settings
        if node.nodeType == Node.ELEMENT_NODE:
            if (node.nodeName == "valve_protocol"):
                self.protocol_name = node.firstChild.nodeValue
        self.name = self.protocol_name

    ## getDescriptor
    #
    # Return a string that describes the command
    #
    def getDescriptor(self):
        return self.name

    ## getDetails
    #
    # Return a a list with details for display in a descriptor table
    #
    def getDetails(self):
        return [ ["Valve Command", ""],
                 ["Name", self.name] ] 
    
    ## __repr__
    #
    def __repr__(self):
        return hdebug.objectToString(self, "sequenceParser.ValveProtocol", ["protocol_name"])

## parseMovieXml
#
# Parses the XML file that describes the movies.
#
# @param movie_xml_filename The name of the XML file.
#
def parseMovieXml(movie_xml_filename):
    xml = minidom.parse(movie_xml_filename)
    sequence = xml.getElementsByTagName("sequence").item(0)

    commands = []
    children = sequence.childNodes
    for child in children:
        if child.nodeType == Node.ELEMENT_NODE:
            if child.tagName == "movie":
                commands.append(Movie(child))
            elif child.tagName == "valve_protocol":
                commands.append(ValveProtocol(child))

    return commands

#
# Testing
# 
if __name__ == "__main__":
    parsed_commands = parseMovieXml("sequence.xml")
    print "Parsed the following commands: "
    for command in parsed_commands:
        print command

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

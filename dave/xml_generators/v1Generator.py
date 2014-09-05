#!/usr/bin/python
#
## @file
#
# Generate XML for Dave given a position list and an experiment description file.
#
# Hazen 05/14
#

import copy
import math
import os

from xml.dom import minidom
from xml.etree import ElementTree
from PyQt4 import QtCore, QtGui

import xml_generators.nodeToDict as nodeToDict
import daveActions

## generate
#
# @param parent The PyQt parent to use when displaying a dialog box.
# @param xml_file The input XML file.
# @param position_file A positions file.
# @param generated_file The name of output file
#
# @return True/False if the XML generation was successful (or not).
#
def generate(parent, xml_file, position_file, generated_file):

    directory = os.path.dirname(xml_file)
    pause = True

    # Load position data
    pos_fp = open(position_file, "r")
    x_pos = []
    y_pos = []
    while 1:
        line = pos_fp.readline()
        if not line: break
        [x, y] = line.split(",")
        x_pos.append(float(x))
        y_pos.append(float(y))
    pos_fp.close()

    xml_in = ElementTree.parse(xml_file).getroot()

    # Load "header" info.
    x_offset = nodeToDict.gf("x_offset", [float], 0.0)(xml_in)
    y_offset = nodeToDict.gf("y_offset", [float], 0.0)(xml_in)
    delay = nodeToDict.gf("delay", [int], 0)(xml_in)

    # Create instances of all the supported actions
    # in the order in which they should occur.
    da_actions = [daveActions.DAMoveStage(),
                  daveActions.DASetFocusLockTarget(),
                  daveActions.DAFindSum(),
                  daveActions.DARecenterPiezo(),
                  daveActions.DASetParameters(),
                  daveActions.DASetProgression(),
                  daveActions.DASetDirectory(),
                  daveActions.DADelay(),
                  daveActions.DAPause(),
                  daveActions.DATakeMovie()]

    # Generate output xml tree.
    xml_out = ElementTree.Element("sequence")
    first_movie = True
    for pass_number, pass_node in enumerate([x for x in xml_in if (x.tag == "pass")]):

        # Create a new block for this pass.
        pass_block = ElementTree.SubElement(xml_out, "branch")
        pass_block.set("name", "pass " + str(pass_number))

        for i in range(len(x_pos)):
            mx = x_pos[i] + x_offset
            my = y_pos[i] + y_offset
            
            for movie_number, movie_node in enumerate([x for x in pass_node if (x.tag == "movie")]):

                #
                # Check if we need to get a filename for a power progression.
                #
                # This modifies the original node so that we don't have to keep
                # selecting a filename.
                #
                pnode = movie_node.find("progression")
                if pnode is not None:
                    if (pnode.find("type").text == "file"):
                        if pnode.find("filename") is None:
                            filename = str(QtGui.QFileDialog.getOpenFileName(parent,
                                                                             movie_node.find("name").text + " Power File",
                                                                             directory,
                                                                             "*.power"))
                            directory = os.path.dirname(filename)
                            field = ElementTree.SubElement(pnode, "filename")
                            field.text = filename

                # Create dictionary for node.
                movie_dict = nodeToDict.movieNodeToDict(movie_node)

                # Add extra information to complete the movie node.
                total_delay = delay
                if "delay" in movie_dict:
                    total_delay += movie_dict["delay"]
                if (total_delay > 0):
                    movie_dict["delay"] = total_delay

                if first_movie:
                    movie_dict["pause"] = True
                    first_movie = False

                if (movie_number == 0):
                    movie_dict["stage_x"] = mx
                    movie_dict["stage_y"] = my

                if "name" in movie_dict:
                    # Create new block for this movie.
                    movie_block = ElementTree.SubElement(pass_block, "branch")
                    movie_block.set("name", movie_dict["name"] + " " + str(pass_number) + " " + str(i))

                    for action in da_actions:
                        node = action.createETree(movie_dict)
                        if node is not None:
                            movie_block.append(node)

    # Save to output XML file.
    out_fp = open(generated_file, "w")

    #
    # Thank you StackOverflow..
    # http://stackoverflow.com/questions/17402323/use-xml-etree-elementtree-to-write-out-nicely-formatted-xml-files
    #
    rough_string = ElementTree.tostring(xml_out, 'utf-8')

    reparsed = minidom.parseString(rough_string)
    out_fp.write(reparsed.toprettyxml(indent="  ", encoding = "ISO-8859-1"))
    out_fp.close()

    return generated_file

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

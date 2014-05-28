#!/usr/bin/python
#
## @file
#
# Generate XML for Dave given a position list and an experiment description file.
#
# Hazen 05/14
#

import math
import os

from xml.dom import minidom
from xml.etree import ElementTree
from PyQt4 import QtCore, QtGui

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
    x_offset = float(xml_in.find("x_offset").text)
    y_offset = float(xml_in.find("y_offset").text)
    delay = 0
    if xml_in.find("delay") is not None:
        delay = int(xml_in.find("delay"))

    # Generate output xml tree.
    xml_out = ElementTree.Element("sequence")
    first_movie = True
    for pass_number, pass_node in enumerate([x for x in xml_in if (x.tag == "pass")]):
        for i in range(len(x_pos)):
            mx = x_pos[i] + x_offset
            my = y_pos[i] + y_offset
            
            for movie_number, temp_node in enumerate([x for x in pass_node if (x.tag == "movie")]):

                # Create a copy so that we don't change the original.
                movie_node = copy.deepcopy(temp_node)

                # Add extra information to complete the movie node.
                field = ElementTree.SubElement(movie_node, "base_delay")
                field.text = delay

                if first_movie:
                    field = ElementTree.SubElement(movie_node, "first_movie")
                    field.text = str(first_movie)

                if (movie_number > 0):
                    field = ElementTree.SubElement(movie_node, "stage_x")
                    field.text = str(mx)
                    field = ElementTree.SubElement(movie_node, "stage_y")
                    field.text = str(my)

                # Create new block for this movie.
                block = ElementTree.SubElement(xml_out, "block")

                # Create move stage action.
                if (movie_number == 0):
                    da_move_stage = daveActions.DAMoveStage()
                    da_move_stage.setProperty("stage_x", mx)
                    da_move_stage.setProperty("stage_y", my)
                    da_move_stage.addToETree(block)

                # Create set lock target action.
                lock_target = movie_node.find("lock_target")
                if lock_target is not None:
                    da_set_focus_lock_target = daveActions.DASetFocusLockTarget()
                    da_set_focus_lock_target.setProperty("lock_target", float(lock_target.text))
                    da_set_focus_lock_target.addToETree(block)

                # Create find sum action.
                find_sum = movie_node.find("find_sum")
                if find_sum is not None:
                    min_sum = float(find_sum.text)
                    if (min_sum > 0.0):
                        da_find_sum = daveActions.DAFindSum()
                        da_find_sum.setProperty("min_sum", min_sum)
                        da_find_sum.addToETree(block)

                # Create recenter action.
                if movie_node.find("recenter") is not None:
                    da_recenter_piezo = daveActions.DARecenterPiezo()
                    da_recenter_piezo.addToETree(block)

                # Create progression action.
                if movie_node.find("progression") is not None:
                    prog_node = movie_node.find("progression")
                    type = prog_node.find("type").text

                # Create parameters action.
                parameters = movie_node.find("parameters")
                if parameters is not None:
                    da_set_parameters = daveActions.DASetParameters()
                    da_set_parameters.setProperty("parameters", parameters.text)
                    da_set_parameters.addToETree(block)

                # Create directory action.
                directory = movie_node.find("directory")
                if directory is not None:
                    da_set_directory = daveActions.DASetDirectory()
                    da_set_directory.setProperty("directory", directory)
                    da_set_directory.addToETree(block)

                # Create delay action.
                extra_delay = movie_node.find("delay")
                if extra_delay is not None:
                    total_delay = delay + int(extra_delay.text)
                    if (total_delay > 0):
                        da_delay = daveActions.DADelay()
                        da_delay.setProperty("delay", total_delay)
                        da_delay.addToETree(block)

                # Create pause action.
                if first_movie or movie_node.find("pause") is not None:
                    da_pause = daveActions.DAPause()
                    da_pause.addToETree(block)

                # Create movie action.
                movie_length = int(movie_node.find("length").text)
                if (movie_length > 0):
                    da_take_movie = daveActions.DATakeMovie()
                    movie_name = movie_node.find("name").text
                    da_take_movie.setProperty("name", movie_name + "_" + str(pass_number) + "_" + str(i))
                    da_take_movie.setProperty("length", movie_length)
                    min_spots = movie_node.find("min_spots")
                    if min_spots is not None:
                        da_take_movie.setProperty("min_spots", int(min_spots.text))
                    da_take_movie.addToETree(block)

                first_movie = False

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

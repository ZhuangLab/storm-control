#!/usr/bin/python
#
## @file
#
# Generate XML for Dave given a position list
# and an experiment description file.
#
# Hazen 12/10
#

import math
import os
from xml.dom import minidom, Node
from PyQt4 import QtCore, QtGui

nl = "\n"

## writeSingleMovie
#
# Writes the xml for a single movie to the XML file.
#
# @param fp The XML file pointer.
# @param movie The XML describing a single movie.
#
def writeSingleMovie(fp, movie):
    movie.writexml(fp)

## generateXML
#
# @param descriptor_file The XML experiment description file.
# @param position_file A text file containing a list of positions to take the movies at.
# @param output_file The file to save the movie XML to.
# @param directory The working directory.
# @param parent A PyQt object to use as the parent for dialog boxes.
#
def generateXML(descriptor_file, position_file, output_file, directory, parent):
    pause = 1
    pos_fp = open(position_file, "r")
    out_fp = open(output_file, "w")

    # Load position data
    x_pos = []
    y_pos = []
    while 1:
        line = pos_fp.readline()
        if not line: break
        [x, y] = line.split(",")
        x_pos.append(float(x))
        y_pos.append(float(y))

    # Load experiment descriptor file
    dom = minidom.parse(descriptor_file)
    xml = dom.getElementsByTagName("experiment").item(0)

    x_offset = float(xml.getElementsByTagName("x_offset").item(0).firstChild.nodeValue)
    y_offset = float(xml.getElementsByTagName("y_offset").item(0).firstChild.nodeValue)

    # Determine minimum delay time (in milliseconds)
    temp = xml.getElementsByTagName("delay")
    if (len(temp) > 0):
        delay_time = int(temp.item(0).firstChild.nodeValue)
    else:
        delay_time = 500

    # Determine stage speed (in units of mm/second)
    temp = xml.getElementsByTagName("stage_speed")
    if (len(temp) > 0):
        stage_speed = float(temp.item(0).firstChild.nodeValue)
    else:
        stage_speed = 2.0

    passes = xml.getElementsByTagName("pass")

    # Write the XML
    out_fp.write("<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>" + nl)
    out_fp.write("<sequence>" + nl)

    first_movie = True
    pass_number = 0
    for a_pass in passes:
        old_mx = 0.0
        old_my = 0.0
        power_filenames = {}
        for i in range(len(x_pos)):
            mx = x_pos[i] + x_offset
            my = y_pos[i] + y_offset
            for j, movie in enumerate(a_pass.getElementsByTagName("movie")):

                # sort out the proper name for the movie
                temp = movie.cloneNode(True)
                movie_name = str(temp.getElementsByTagName("name").item(0).firstChild.nodeValue)
                temp_name = movie_name + "_" + str(pass_number) + "_" + str(i)
                temp.getElementsByTagName("name").item(0).firstChild.nodeValue = temp_name

                # if this is file type progression, then have the user
                # specify the name of the file to use & add to the xml
                if not (movie_name in power_filenames):
                    progression = temp.getElementsByTagName("progression")
                    if (len(progression) > 0):
                        type = progression[0].getElementsByTagName("type").item(0).firstChild.nodeValue
                        if (type == "file"):
                            power_filenames[movie_name] = str(QtGui.QFileDialog.getOpenFileName(parent,
                                                                                               movie_name + " Power File",
                                                                                               directory,
                                                                                               "*.power"))
                            directory = os.path.dirname(power_filenames[movie_name])

                # if we have a power filename for this movie, verify that this movie has 
                # a progression of type "file" and if so, insert the filename into the xml.
                if (movie_name in power_filenames):
                    progression = temp.getElementsByTagName("progression")[0]
                    type = progression.getElementsByTagName("type").item(0).firstChild.nodeValue
                    if (type == "file"):
                        filename = dom.createElement("filename")
                        filename.appendChild(dom.createTextNode(power_filenames[movie_name]))
                        progression.appendChild(filename)

                # Add delay element, if it doesn't exist
                delay = temp.getElementsByTagName("delay")
                if(len(delay) == 0):
                    delay = dom.createElement("delay")
                    if (j == 0) and (not first_movie):
                        delay.appendChild(dom.createTextNode(str(delay_time)))
                    else:
                        delay.appendChild(dom.createTextNode(str(200)))
                    temp.appendChild(delay)

                # Add additional delay to allow for stage motion between positions.
                if (j == 0) and (not first_movie):
                    dist_x = mx - old_mx
                    dist_y = my - old_my
                    dist = math.sqrt(dist_x*dist_x + dist_y*dist_y)
                    time = int(dist/stage_speed)
                    if (hasattr(delay, "firstChild")):
                        delay.firstChild.nodeValue = str(time + int(delay.firstChild.nodeValue))
                    else:
                        delay.item(0).firstChild.nodeValue = str(time + int(delay.item(0).firstChild.nodeValue))

                # set delay of the first movie to zero
                if first_movie:
                    if (hasattr(delay, "firstChild")):
                        delay.firstChild.nodeValue = "0"
                    else:
                        delay.item(0).firstChild.nodeValue = "0"

                # remove find_sum and recenter if this is the first movie
                if first_movie:
                    find_sum = temp.getElementsByTagName("find_sum")
                    if (len(find_sum) > 0):
                        temp.getElementsByTagName("find_sum").item(0).firstChild.nodeValue = 0
                    recenter = temp.getElementsByTagName("recenter")
                    if (len(recenter) > 0):
                        temp.getElementsByTagName("recenter").item(0).firstChild.nodeValue = 0

                # add pause element
                pause = dom.createElement("pause")
                temp.appendChild(pause)
                if first_movie:
                    pause.appendChild(dom.createTextNode("1"))
                    first_movie = False
                else:
                    pause.appendChild(dom.createTextNode("0"))

                # add stage position elements
                stagex = dom.createElement("stage_x")
                stagex.appendChild(dom.createTextNode(str(mx)))
                temp.appendChild(stagex)

                stagey = dom.createElement("stage_y")
                stagey.appendChild(dom.createTextNode(str(my)))
                temp.appendChild(stagey)

                # write the xml for this movie
                writeSingleMovie(out_fp, temp)
                out_fp.write(nl)

            # record current stage position
            old_mx = mx
            old_my = my

            out_fp.write(nl)
        out_fp.write(nl)
        pass_number += 1
        
    out_fp.write("</sequence>" + nl)
    out_fp.close()

if __name__ == "__main__":
    import sys
    generateXML(sys.argv[1], sys.argv[2], sys.argv[3])


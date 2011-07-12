#!/usr/bin/python
#
# Generate XML for Dave given a position list
# and an experiment description file.
#
# Hazen 12/10
#

import os
from xml.dom import minidom, Node
from PyQt4 import QtCore, QtGui

nl = "\n"

def writeSingleMovie(fp, movie):
    movie.writexml(fp)

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
    temp = xml.getElementsByTagName("delay")
    if (len(temp) > 0):
        delay_time = int(temp.item(0).firstChild.nodeValue)
    else:
        delay_time = 5000

    passes = xml.getElementsByTagName("pass")

    # Write the XML
    out_fp.write("<?xml version=\"1.0\" encoding=\"ISO-8859-1\"?>" + nl)
    out_fp.write("<sequence>" + nl)

    first_movie = True
    pass_number = 0
    for a_pass in passes:
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

                # add delay element, if it doesn't exist
                delay = temp.getElementsByTagName("delay")
                if(len(delay) == 0):
                    delay = dom.createElement("delay")
                    if (j == 0) and (not first_movie):
                        delay.appendChild(dom.createTextNode(str(delay_time)))
                    else:
                        delay.appendChild(dom.createTextNode(str(1000)))
                    temp.appendChild(delay)

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
            out_fp.write(nl)
        out_fp.write(nl)
        pass_number += 1
        
    out_fp.write("</sequence>" + nl)
    out_fp.close()

if __name__ == "__main__":
    import sys
    generateXML(sys.argv[1], sys.argv[2], sys.argv[3])


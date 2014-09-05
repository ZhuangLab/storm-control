#!/usr/bin/python
#
## @file
#
# Based on a quick read of the recipe xml file, chooses
# the appropriate generator to convert the xml into a
# series of DaveAction XMLs.
#
# Hazen 05/14
#

import os

from xml.etree import ElementTree
from PyQt4 import QtCore, QtGui

import xml_generators.v1Generator as v1Generator
import xml_generators.v2Generator as v2Generator


## generate
#
# @param parent The PyQt parent to use when displaying a dialog box.
# @param xml_file The input xml file
#
# @return generated_file The output xml file, or None if there was an error or generation was cancelled.
#
def generate(parent, xml_file):
    is_good = False

    directory = os.path.dirname(xml_file)
    root_element = ElementTree.parse(xml_file).getroot().tag

    # Version 1 XML format.
    if (root_element == "experiment"):
        position_file = str(QtGui.QFileDialog.getOpenFileName(parent,
                                                              "Positions File", 
                                                              directory, 
                                                              "*.txt"))
        if (len(position_file)>0):
            generated_file = str(QtGui.QFileDialog.getSaveFileName(parent,
                                                                   "Generated File", 
                                                                   directory, 
                                                                   "*.xml"))
            if (len(generated_file)>0):
                is_good = v1Generator.generate(parent, xml_file, position_file, generated_file)

    # Version 2 XML format.
    elif (root_element == "recipe"):
        xml_parser = v2Generator.XMLRecipeParser(xml_filename = xml_file)
        xml_parser.parseXML()
        generated_file = xml_parser.writtenXMLPath()
        is_good = not (generated_file == "")
    if is_good:
        return generated_file
    else:
        return None


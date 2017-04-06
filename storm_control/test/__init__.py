#!/usr/bin/env python

import os

def dataDirectory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/")

def daveXmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "dave_xml", filename)

def halXmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "hal", filename)

def kilroyXmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "kilroy_xml", filename)

def logDirectory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/")

def steveXmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "steve_xml", filename)
    
def xmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "xml", filename)

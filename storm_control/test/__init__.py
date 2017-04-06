#!/usr/bin/env python

import os

def halXmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "hal_xml", filename)

def logDirectory():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs/")
    
def xmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "xml", filename)

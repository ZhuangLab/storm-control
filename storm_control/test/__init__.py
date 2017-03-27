#!/usr/bin/env python

import os

def xmlFilePathAndName(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "xml", filename)

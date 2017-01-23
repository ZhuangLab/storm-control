#!/usr/bin/python
#
## @file
#
# For running modules outside of HAL.
#
# Hazen 03/14
#

# Add current storm-control directory to sys.path
import imp
imp.load_source("setPath", "../sc_library/setPath.py")

import importlib
import sys
from PyQt5 import QtWidgets

import storm_control.sc_library.parameters as params

def runModule(module_type, setup_name = False):
    app = QtWidgets.QApplication(sys.argv)

    general_parameters = params.halParameters("settings_default.xml")
    if setup_name:
        general_parameters.set("setup_name", setup_name)
    else:
        setup_name = general_parameters.get("setup_name")
    hardware = params.hardware("xml/" + setup_name + "_hardware.xml")

    found = False
    for module in hardware.get("modules").getProps():
        if (module.get("hal_type") == module_type):
            a_module = importlib.import_module("storm_control.hal4000." + module.get("module_name"))
            a_class = getattr(a_module, module.get("class_name"))
            instance = a_class(module.get("parameters", False), general_parameters, None)

            params.setDefaultParameters(general_parameters)
            setup_parameters = params.halParameters("xml/" + setup_name + "_default.xml")

            instance.newParameters(setup_parameters)
            instance.show()
            found = True
            break

    if found:
        app.exec_()
        instance.cleanup()
    else:
        print(module_type, "not found for", setup_name, "setup")

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

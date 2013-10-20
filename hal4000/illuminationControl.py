#!/usr/bin/python
#
## @file
#
# Run illumination control only
#
# Hazen 3/12
#

import sys
from PyQt4 import QtGui

import halLib.parameters as params

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")
    setup_name = parameters.setup_name
    parameters = params.Parameters(setup_name + "_default.xml", is_HAL = True)
    parameters.setup_name = setup_name
    illumination = __import__('illumination.' + setup_name.lower() + 'IlluminationControl', globals(), locals(), [setup_name], -1)
    illum = illumination.AIlluminationControl(parameters, None)
    shutterControl = __import__('illumination.' + setup_name + 'ShutterControl', globals(), locals(), [setup_name], -1)
    shutter_control = shutterControl.AShutterControl(illum.power_control.powerToVoltage)
    illum.show()
    app.exec_()

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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

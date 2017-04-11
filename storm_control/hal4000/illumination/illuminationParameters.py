#!/usr/bin/env python
"""
Custom parameter types for illumination.

Hazen 04/17
"""

import ast

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_library.parameters as params

#import storm_control.hal4000.illumination.buttonEditor as buttonEditor


class IlluminationParameterException(halExceptions.HalException):
    pass


class ParameterPowerButtons(params.ParameterCustom):

    def __init__(self, **kwds):
        super().__init__(**kwds)
        #self.editor = buttonEditor.ParametersTablePowerButtonEditor
        
    def toType(self, new_value):
        if isinstance(new_value, str):
            new_value = ast.literal_eval(new_value)

        if not isinstance(new_value, (list, tuple)):
            msg = "Can't convert '" + str(type(new_value)) + "' to power buttons."
            raise IlluminationParameterException(msg)

        return new_value


# FIXME: Add an editor for these?
class ParameterDefaultPowers(params.ParameterCustom):

    def toString(self):
        return ",".join(map(lambda x: "{0:.3f}".format(x), self.value))
        
    def toType(self, new_value):
        if isinstance(new_value, str):
            new_value = new_value.split(",")

        if not isinstance(new_value, (list, tuple)):
            msg = "Can't convert '" + str(type(new_value)) + "' to a list of floats."
            raise IlluminationParameterException(msg)

        if self.value is not None:
            if (len(new_value) != len(self.value)):
                raise IlluminationParameterException("List is not the right length.")
        
        return list(map(float, new_value))


# FIXME: Add an editor for these?
class ParameterOnOffStates(params.ParameterCustom):

    def toString(self):
        return ",".join(map(str, self.value))
        
    def toType(self, new_value):
        if isinstance(new_value, str):
            values = []
            for elt in new_value.split(","):
                if (elt.lower() == "true"):
                    values.append(True)
                else:
                    values.append(False)
            new_value = values
            
        if not isinstance(new_value, (list, tuple)):
            msg = "Can't convert '" + str(type(new_value)) + "' to a list of booleans."
            raise IlluminationParameterException(msg)

        if self.value is not None:
            if (len(new_value) != len(self.value)):
                raise IlluminationParameterException("List is not the right length.")

        return list(map(bool, new_value))


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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

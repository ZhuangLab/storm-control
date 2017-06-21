#!/usr/bin/env python
"""
The filter wheel control UI.

Hazen Babcock 06/17
"""

from PyQt5 import QtWidgets

import storm_control.sc_library.parameters as params

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule

import storm_control.hal4000.qtdesigner.filter_wheel_ui as filterWheelUi


class FilterWheelView(halDialog.HalDialog):
    """
    Manages the filter wheel GUI.

    This assumes that the filter wheel hardware is zero indexed.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.buttons = []
        self.filter_fn = None
        self.parameters = params.StormXMLObject()
        self.scan_fn = None

        # Load UI
        self.ui = filterWheelUi.Ui_Dialog()
        self.ui.setupUi(self)

        # Create buttons.
        layout = QtWidgets.QHBoxLayout(self.ui.filtersGroupBox)
        layout.setContentsMargins(1,1,1,1)
        layout.setSpacing(1)
        filter_names = configuration.get("filters").split(",")
        for name in filter_names:
            button = QtWidgets.QPushButton(name, self.ui.filtersGroupBox)
            button.setAutoExclusive(True)
            button.setCheckable(True)
            button.clicked.connect(self.handleClicked)
            layout.addWidget(button)
            self.buttons.append(button)

        # Set to minimum size & fix.
        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        
        self.parameters.add(params.ParameterSetString(description ="Current filter",
                                                      name = "current_filter",
                                                      value = filter_names[0],
                                                      allowed = filter_names))
        self.setEnabled(False)

    def getParameters(self):
        return self.parameters
    
    def handleClicked(self, boolean):
        for i, button in enumerate(self.buttons):
            if button.isChecked():
                button.setStyleSheet("QPushButton { color: red}")
                # FIXME: This won't work if two filters have the same name.
                self.parameters.setv("current_filter", button.text())
                self.filter_fn.setCurrentPosition(i)
            else:
                button.setStyleSheet("QPushButton { color: black}")

    def newParameters(self, parameters):
        self.parameters = parameters
        if self.filter_fn is not None:
            self.setCurrentFilter()

    def setCurrentFilter(self):
        for button in self.buttons:
            if (button.text() == self.parameters.get("current_filter")):
                button.click()

    def setFunctionality(self, filter_fn):
        self.filter_fn = filter_fn
        self.setEnabled(True)
        self.setCurrentFilter()


class FilterWheel(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.view = FilterWheelView(module_name = self.module_name,
                                    configuration = module_params.get("configuration"))
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " filter wheel")

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setFunctionality(response.getData()["functionality"])

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Filter Wheel",
                                                           "item data" : "filter wheel"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("filter_wheel_fn")}))

            self.sendMessage(halMessage.HalMessage(m_type = "initial parameters",
                                                   data = {"parameters" : self.view.getParameters()}))            

        elif message.isType("new parameters"):
            p = message.getData()["parameters"]
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"old parameters" : self.view.getParameters().copy()}))
            self.view.newParameters(p.get(self.module_name))
            message.addResponse(halMessage.HalMessageResponse(source = self.module_name,
                                                              data = {"new parameters" : self.view.getParameters()}))

        elif message.isType("show"):
            if (message.getData()["show"] == "filter wheel"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()


#
# The MIT License
#
# Copyright (c) 2017 Babcock Lab, Harvard University
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

#!/usr/bin/env python
"""
As all the HAL tests are basically the same, this 
factors out what is common to all of them.

Hazen 04/17
"""
import sys

from PyQt5 import QtWidgets

import storm_control.hal4000.hal4000 as hal4000
import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params
import storm_control.test as test

def halTest(config_xml = "", class_name = "Testing", test_module = "", show_gui = False):

    app = QtWidgets.QApplication(sys.argv)
    
    config = params.config(test.halXmlFilePathAndName(config_xml))

    # Add the class that will actually do the testing.
    c_test = config.addSubSection("modules.testing")
    c_test.add("class_name", class_name)
    c_test.add("module_name", test_module)
    
    hdebug.startLogging(test.logDirectory(), "hal4000")
    
    hal = hal4000.HalCore(config = config,
                          testing_mode = True,
                          show_gui = show_gui)
    
    app.exec_()
    app = None

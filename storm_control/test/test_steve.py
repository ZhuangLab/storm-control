#!/usr/bin/env python
"""
Steve tests.
"""
import pytestqt

import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params

import storm_control.steve.steve as steve

import storm_control.test as test
import storm_control.test.hal.halSteveTest as halSteveTest


def test_steve_hal(qtbot):
    hal = halSteveTest.HalSteveTest(config_xml = "none_tcp_config.xml")
    hal.run()
    
    parameters = params.parameters(test.steveXmlFilePathAndName("test_default.xml"))
    hdebug.startLogging(test.logDirectory(), "steve")
    mainw = steve.Window(parameters)
    mainw.show()

    qtbot.addWidget(mainw)

    # Run for about 0.5 seconds.
    qtbot.wait(500)

    hal.stop()
    


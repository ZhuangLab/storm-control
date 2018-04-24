#!/usr/bin/env python
"""
Test HAL error handling.
"""
import os
import pytestqt
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_analysis.sa_library.datareader as datareader

import storm_control.hal4000.hal4000 as hal4000
import storm_control.sc_library.hdebug as hdebug
import storm_control.sc_library.parameters as params
import storm_control.test as test

from storm_control.test.hal.standardHalTest import halTest

def test_hal_error_1(qtbot):
    """
    Test handling of an error in a module.
    """
    hdebug.startLogging(test.logDirectory(), "hal4000")
        
    config = params.config(test.halXmlFilePathAndName("none_hal_error_1.xml"))
    hal = hal4000.HalCore(config = config, show_gui = False)

    qtbot.addWidget(hal)
    qtbot.wait(500)

    assert not hal.running

def test_hal_error_2(qtbot):
    """
    Test handling of an error in a HAL worker.
    """
    hdebug.startLogging(test.logDirectory(), "hal4000")
        
    config = params.config(test.halXmlFilePathAndName("none_hal_error_2.xml"))
    hal = hal4000.HalCore(config = config, show_gui = False)

    qtbot.addWidget(hal)
    qtbot.wait(500)

    assert not hal.running

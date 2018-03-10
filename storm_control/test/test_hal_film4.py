#!/usr/bin/env python
import pytestqt
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.hal4000.hal4000 as hal4000
import storm_control.sc_library.parameters as params
import storm_control.test as test

def test_hal_film(qtbot, mock):
    """
    Test filming without actually recording.
    """

    # 'Fix' question boxes to always return yes.
    #
    # https://github.com/pytest-dev/pytest-qt/issues/18
    #
    mock.patch.object(QtWidgets.QMessageBox, 'question', return_value = QtWidgets.QMessageBox.Yes)
    
    config = params.config(test.halXmlFilePathAndName("none_classic_config.xml"))
    hal = hal4000.HalCore(config = config)

    # Get UI element we need.
    mainWindow = hal.findChild(QtWidgets.QMainWindow, "MainWindow")
    assert(mainWindow is not None)
    saveMovieCheckBox = hal.findChild(QtWidgets.QCheckBox, "saveMovieCheckBox")
    assert(saveMovieCheckBox is not None)
    recordButton = hal.findChild(QtWidgets.QPushButton, "recordButton")
    assert(recordButton is not None)

    # Start HAL.
    qtbot.addWidget(hal)
    qtbot.waitForWindowShown(mainWindow)
    qtbot.wait(100)
    
    # Uncheck save movie and press record.
    qtbot.mouseClick(saveMovieCheckBox, QtCore.Qt.LeftButton)
    qtbot.mouseClick(recordButton, QtCore.Qt.LeftButton)

    # Wait a second for the film to complete, then exit.
    qtbot.wait(1000)
    

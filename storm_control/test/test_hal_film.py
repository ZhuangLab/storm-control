#!/usr/bin/env python
"""
Filming tests.
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


def test_hal_film_1():

    # This is expected to record a movie called 'movie_01.dax'
    halTest(config_xml = "none_classic_config.xml",
            class_name = "FilmTest1",
            test_module = "storm_control.test.hal.film_tests")

    # Check that the movie is the right length.
    movie = datareader.inferReader(os.path.join(test.dataDirectory(), "movie_01.dax"))
    assert(movie.filmSize() == [512, 512, 10])

    
def test_hal_film_2():

    # This is expected to record several movies with names starting with 'movie_02'
    halTest(config_xml = "none_classic_config.xml",
            class_name = "FilmTest2",
            test_module = "storm_control.test.hal.film_tests")

    # Check that the movies are the right length.
    for name, size in [["movie_02.dax", [512, 512, 10]],
                       ["movie_02_average.dax", [512, 512, 1]],
                       ["movie_02_interval.dax", [508, 256, 2]],
                       ["movie_02_slice1.dax", [64, 65, 10]]]:
        movie = datareader.inferReader(os.path.join(test.dataDirectory(), name))
        assert(movie.filmSize() == size)

        
def test_hal_film_3():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "FilmTest3",
            test_module = "storm_control.test.hal.film_tests")


def test_hal_film_4(qtbot, mock):
    """
    Test filming without actually recording.
    """

    # 'Fix' question boxes to always return yes.
    #
    # https://github.com/pytest-dev/pytest-qt/issues/18
    #
    mock.patch.object(QtWidgets.QMessageBox, 'question', return_value = QtWidgets.QMessageBox.Yes)

    hdebug.startLogging(test.logDirectory(), "hal4000")
        
    config = params.config(test.halXmlFilePathAndName("none_classic_config.xml"))
    hal = hal4000.HalCore(config = config)

    # Get UI elements we need.
    mainWindow = hal.findChild(QtWidgets.QMainWindow, "MainWindow")
    saveMovieCheckBox = hal.findChild(QtWidgets.QCheckBox, "saveMovieCheckBox")
    recordButton = hal.findChild(QtWidgets.QPushButton, "recordButton")

    # Start HAL.
    qtbot.addWidget(hal)
    qtbot.waitForWindowShown(mainWindow)
    qtbot.wait(100)
    
    # Uncheck save movie and press record.
    qtbot.mouseClick(saveMovieCheckBox, QtCore.Qt.LeftButton)
    qtbot.mouseClick(recordButton, QtCore.Qt.LeftButton)

    # Wait a second for the film to complete, then exit.
    qtbot.wait(1000)


def test_hal_film_5():
    """
    Test repeated film acquisition.
    """
    halTest(config_xml = "none_classic_config.xml",
            class_name = "FilmTest4",
            test_module = "storm_control.test.hal.film_tests")

    # Check that the final movie is correct.
    movie = datareader.inferReader(os.path.join(test.dataDirectory(), "movie_04.dax"))
    assert(movie.filmSize() == [512, 512, 1])
    

def test_hal_film_6():

    # This is expected to record a movie called 'movie_01.dax'
    halTest(config_xml = "none_tcp_config_low_qpd_signal.xml",
            class_name = "FilmTest5",
            test_module = "storm_control.test.hal.film_tests",
            show_gui = True)

    # Check that the movie is the right length.
    movie = datareader.inferReader(os.path.join(test.dataDirectory(), "movie_01.dax"))
    assert(movie.filmSize() == [512, 512, 10])
    

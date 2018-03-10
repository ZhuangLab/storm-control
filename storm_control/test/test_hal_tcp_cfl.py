#!/usr/bin/env python
"""
Check focus lock tests.
"""
from storm_control.test.hal.standardHalTest import halTest


def test_hal_tcp_cfl_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "CheckFocusLock1",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_cfl_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "CheckFocusLock2",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_cfl_3():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "CheckFocusLock3",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_cfl_4():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "CheckFocusLock4",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_cfl_5():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "CheckFocusLock5",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_cfl_6():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "CheckFocusLock6",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_cfl_7():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "CheckFocusLock7",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


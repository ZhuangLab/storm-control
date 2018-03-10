#!/usr/bin/env python
"""
Test setting progressions.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_tcp_sp_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetProgression1",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_sp_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetProgression2",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_sp_3():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetProgression3",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_sp_4():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetProgression4",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_sp_5():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetProgression5",
            show_gui = True,            
            test_module = "storm_control.test.hal.tcp_tests")

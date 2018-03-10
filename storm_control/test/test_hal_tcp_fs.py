#!/usr/bin/env python
"""
Focus lock find sum tests.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_tcp_fs_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "FindSum1",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_fs_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "FindSum2",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_fs_3():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "FindSum3",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_fs_4():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "FindSum4",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")

#!/usr/bin/env python
"""
Test setting parameters.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_tcp_sp_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetParameters1",
            test_module = "storm_control.test.hal.tcp_tests")

    
def test_hal_tcp_sp_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetParameters2",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_sp_3():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetParameters3",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_sp_4():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetParameters4",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_sp_5():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetParameters5",
            test_module = "storm_control.test.hal.tcp_tests")


#!/usr/bin/env python
"""
Test get objective.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_go_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "GetObjective1",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_go_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "GetObjective2",
            test_module = "storm_control.test.hal.tcp_tests")

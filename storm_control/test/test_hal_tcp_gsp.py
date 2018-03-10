#!/usr/bin/env python
"""
Test getting the stage position.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_gsp_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "GetStagePosition1",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_gsp_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "GetStagePosition2",
            test_module = "storm_control.test.hal.tcp_tests")

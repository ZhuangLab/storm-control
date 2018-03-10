#!/usr/bin/env python
"""
Mosaic tests.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_gms_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "GetMosaicSettings1",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_gms_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "GetMosaicSettings2",
            test_module = "storm_control.test.hal.tcp_tests")

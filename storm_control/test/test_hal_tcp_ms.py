#!/usr/bin/env python
"""
Test move stage.
"""
from storm_control.test.hal.standardHalTest import halTest


def test_hal_ms_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "MoveStage1",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_ms_2():

    halTest(config_xml = "none_tcp_config_broken_stage.xml",
            class_name = "MoveStage2",
            test_module = "storm_control.test.hal.tcp_tests")

#!/usr/bin/env python
"""
Test parameter file IO.
"""

from storm_control.test.hal.standardHalTest import halTest

def test_hal_params_1():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "ParamTest1",
            test_module = "storm_control.test.hal.param_tests")


def test_hal_params_2():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "ParamTest2",
            test_module = "storm_control.test.hal.param_tests")


def test_hal_params_3():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "ParamTest3",
            test_module = "storm_control.test.hal.param_tests")


def test_hal_params_4():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "ParamTest4",
            test_module = "storm_control.test.hal.param_tests")


def test_hal_params_5():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "ParamTest5",
            test_module = "storm_control.test.hal.param_tests")

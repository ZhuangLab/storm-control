#!/usr/bin/env python

from storm_control.test.hal.standardHalTest import halTest

def test_hal_params():
    halTest(config_xml = "none_classic_config.xml",
            class_name = "ParamTest2",
            test_module = "storm_control.test.hal.param_tests")

if (__name__ == "__main__"):
    test_hal_params()

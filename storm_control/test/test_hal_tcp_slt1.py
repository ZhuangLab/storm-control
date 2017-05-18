#!/usr/bin/env python

from storm_control.test.hal.standardHalTest import halTest


def test_hal_tcp_slt1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "SetLockTarget1",
            show_gui = True,
            test_module = "storm_control.test.hal.tcp_tests")


if (__name__ == "__main__"):
    test_hal_tcp_slt1()

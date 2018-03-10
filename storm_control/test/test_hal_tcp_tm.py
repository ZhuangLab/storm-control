#!/usr/bin/env python
"""
Test taking movies.
"""
from storm_control.test.hal.standardHalTest import halTest

def test_hal_tcp_tm_1():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie1",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_2():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie2",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_3():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie3",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_4():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie4",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_5():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie5",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_6():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie6",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_7():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie7",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_8():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie8",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_9():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie9",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_10():

    halTest(config_xml = "none_tcp_config.xml",
            class_name = "TakeMovie10",
            test_module = "storm_control.test.hal.tcp_tests")


def test_hal_tcp_tm_11():

    halTest(config_xml = "none_tcp_config_spot_counter.xml",
            class_name = "TakeMovie11",
            test_module = "storm_control.test.hal.tcp_tests")

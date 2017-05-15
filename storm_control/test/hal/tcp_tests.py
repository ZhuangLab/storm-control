#!/usr/bin/env python
import os

import storm_control.sc_library.halExceptions as halExceptions

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testActionsTCP as testActionsTCP
import storm_control.hal4000.testing.testing as testing

import storm_control.test as test


#
# Test "Get Mosaic Settings" message.
#
class GetMosaicSettingsAction1(testActionsTCP.GetMosaicSettings):

    def checkMessage(self, tcp_message):
        assert(tcp_message.getResponse("obj1") == "100x,0.160,0.0,0.0")

class GetMosaicSettings1(testing.TestingTCP):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [GetMosaicSettingsAction1()]

#!/usr/bin/env python

import storm_control.hal4000.testing.testActions as testActions
import storm_control.hal4000.testing.testing as testing

import storm_control.test as test

#
# Check the default parameters.
#
class ParamTest1Action(testActions.GetParameters):

    def checkParameters(self):
        p = self.parameters
        
        assert(p.get("initialized"))
        assert(p.has("camera1"))
        assert(p.has("film"))
        assert(p.has("mosaic"))

class ParamTest1(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [ParamTest1Action(p_name = "default")]


#
# Check that new parameters are not initialized at loading.
#
class ParamTest2Action(testActions.GetParameters):

    def checkParameters(self):
        p = self.parameters
        
        assert(not p.get("initialized"))
        assert(p.has("camera1"))
        assert(p.has("display00"))
        assert(p.has("film"))
        assert(p.has("mosaic"))

class ParamTest2(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        fname = "256x512"
        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName(fname + ".xml")),
                             ParamTest2Action(p_name = fname)]

#
# Check that new parameters are initialized after being set
# as the current parameters.
#
class ParamTest3Action(testActions.GetParameters):

    def checkParameters(self):
        p = self.parameters
        
        assert(p.get("initialized"))
        assert(p.has("camera1"))
        assert(p.has("display00"))
        assert(p.has("film"))
        assert(p.has("mosaic"))

class ParamTest3(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        fname = "256x512"
        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName(fname + ".xml")),
                             testActions.SetParameters(p_name = fname),
                             ParamTest3Action(p_name = fname)]

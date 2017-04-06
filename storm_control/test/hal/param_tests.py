#!/usr/bin/env python

import storm_control.sc_library.halExceptions as halExceptions

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

#
# Check that we can also get parameters by row index.
#
class ParamTest4(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName("256x512.xml")),
                             ParamTest1Action(p_name = 1)]

#
# Check that we fail when two parameter files have the same name.
#
class ParamTest5Action(testActions.GetParameters):

    def finalizer(self):
        if not self.message.hasErrors():
            raise Exception("Error expected for duplicate parameter names.")
        for m_error in self.message.getErrors():
            if not isinstance(m_error.getException(), halExceptions.HalException):
                raise Exception("Unexpected exception type " + str(type(m_error.getException())))
            print(">>", m_error.message)
        self.message.m_errors = []
        self.actionDone.emit()

class ParamTest5(testing.Testing):

    def __init__(self, **kwds):
        super().__init__(**kwds)

        fname = "256x512"
        self.test_actions = [testActions.LoadParameters(filename = test.halXmlFilePathAndName(fname + ".xml")),
                             testActions.LoadParameters(filename = test.halXmlFilePathAndName(fname + ".xml")),
                             ParamTest5Action(p_name = fname)]

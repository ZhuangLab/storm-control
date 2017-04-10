#!/usr/bin/env python
"""
Tests of the parameters object functionality.
"""

import storm_control.test as test

import storm_control.sc_library.parameters as params


def test_parameters_1():

    # Load parameters.
    p1 = params.parameters(test.xmlFilePathAndName("test_parameters.xml"), recurse = True)
    
    # Check a parameter.
    assert (p1.get("camera1.flip_horizontal") == False)

    # Change it's value.
    p1.set("camera1.flip_horizontal", True)

    # Check again.
    assert (p1.get("camera1.flip_horizontal") == True)


def test_parameters_2():

    # Load parameters.
    p1 = params.parameters(test.xmlFilePathAndName("test_parameters.xml"), recurse = True)

    # Copy.
    p2 = p1.copy()

    # Check that p1 and p2 store the same values and have
    # the same structure.
    assert (len(params.difference(p1, p2)) == 0)

    # Change a value in p2.
    p2.set("camera1.flip_horizontal", True)

    # Check that p1 is still the same.
    assert (p1.get("camera1.flip_horizontal") == False)

    # Get the difference between p1 and p2.
    assert (params.difference(p1, p2)[0] == 'camera1.flip_horizontal')
    

def test_parameters_3():

    # Load parameters.
    p1 = params.parameters(test.xmlFilePathAndName("test_parameters.xml"), recurse = True)

    # Test sub-section creation.
    p2 = params.StormXMLObject()
    p2s = p2.addSubSection("camera1", p1.get("camera1").copy())
    p2s.add(params.ParameterInt(name = "test", value = 5))

    # p2 is different then p1 because it has 'test'.
    assert (params.difference(p2.get("camera1"), p1.get("camera1"))[0] == "test")

    # But p1 is not different from p2 because difference() only
    # checks p1 properties that exist in p1.
    assert (len(params.difference(p1.get("camera1"), p2.get("camera1"))) == 0)
    

def test_parameters_4():

    # Load parameters.
    p1 = params.parameters(test.xmlFilePathAndName("test_parameters.xml"), recurse = True)

    # Create another set of parameters with only 1 item.
    p2 = params.StormXMLObject()
    p2.add(params.ParameterString(name = "test_param", value = "bar"))
    p2s = p2.addSubSection("camera1")
    p2s.add(params.ParameterSetBoolean(name = "flip_horizontal", value = True))
    p2s.add(params.ParameterSetBoolean(name = "flip_vertical", value = False))

    # Test copy.
    [p3, ur] = params.copyParameters(p1, p2)

    # Their should be one un-recognized parameter, 'flip_vertical'.
    assert (len(ur) == 1) and (ur[0] == "flip_vertical")

    # 'camera1.flip_horizontal' in p3 should be True.
    assert p3.get("camera1.flip_horizontal")

    # 'test_param' should be 'bar'.
    assert (p3.get("test_param") == "bar")


def test_parameters_5():

    # Load parameters.
    p1 = params.parameters(test.xmlFilePathAndName("test_parameters.xml"),
                           recurse = True,
                           add_filename_param = False)

    # Save.
    p1.saveToFile("temp.xml")

    # Re-load.
    p2 = params.parameters("temp.xml",
                           recurse = True,
                           add_filename_param = False)

    # Check that they are the same.
    assert (len(params.difference(p1, p2)) == 0) and (len(params.difference(p2, p1)) == 0)


def test_parameters_6():
    p1 = params.StormXMLObject()

    s1 = p1.addSubSection("foo")
    s1.add("bar1", "foo1")
        
    s2 = p1.addSubSection("foo.bar")
    s2.add("bar2", "foo2")

    s3 = p1.addSubSection("bar.foo")
    s3.add("foo1", "bar1")
    
    assert(p1.get("foo.bar1") == "foo1")
    assert(p1.get("foo.bar.bar2") == "foo2")
    assert(p1.get("bar.foo.foo1") == "bar1")


def test_parameters_7():
    p1 = params.StormXMLObject()
    v1 = params.ParameterSimple("foo", "bar")
    p1.add(v1)

    p2 = params.StormXMLObject()
    p2.add("foo", p1.getp("foo"))

    p3 = params.StormXMLObject()
    p3.add("foo", p1.getp("foo").copy())

    v1.setv("baz")
    
    assert(p1.get("foo") == "baz")
    assert(p2.get("foo") == "baz")
    assert(p3.get("foo") == "bar")

def test_parameters_8():
    s1 = params.StormXMLObject()
    s2 = params.StormXMLObject()
    p1 = params.Parameter(name = "aa", order = 2)
    p2 = params.Parameter(name = "bb", order = 1)
    p3 = params.Parameter(name = "cc", order = 2)

    s1.addSubSection("dd", s2)
    s1.add(p1)
    s1.add(p2)
    s1.add(p3)

    assert(s1.getSortedAttrs() == ['dd', 'bb', 'aa', 'cc'])

        
if (__name__ == "__main__"):
    test_parameters_1()
    test_parameters_2()
    test_parameters_3()
    test_parameters_4()
    test_parameters_5()
    test_parameters_6()
    test_parameters_7()
    test_parameters_8()

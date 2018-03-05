#!/usr/bin/env python
"""
Test parsing of shutters files.
"""
import numpy

import storm_control.hal4000.illumination.xmlParser as xmlParser

import storm_control.test as test

data_dir = test.dataDirectory()
name_to_id = {"750" : 0,
              "647" : 1,
              "560" : 2}

def test_parser_1():
    """
    Test parsing a correctly formatted XML shutters file.
    """
    [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + "shutters_test_1.xml")

    # Make we got it right.
    assert(s_info.color_data[0] is None)    
    assert(s_info.color_data[1] == [255,0,0])
    assert(s_info.color_data[2] is None)
        
    assert(s_info.frames == 3)
    assert(oversampling == 2)
    assert(numpy.allclose(numpy.zeros(6), waveforms[0]))
    assert(numpy.allclose(numpy.array([0.0, 0.0, 1.0, 1.0, 0.0, 0.0]), waveforms[1]))
    assert(numpy.allclose(numpy.zeros(6), waveforms[2]))


def test_parser_2():
    """
    Test failing on oversampling.
    """
    try:
        [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + "shutters_test_1.xml", can_oversample = False)
    except xmlParser.ShutterXMLException as e:
        print(e)
        return
    
    assert(False)


def test_parser_3():
    """
    Test oversampling defaults.
    """
    [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + "shutters_test_2.xml")
    assert(oversampling == 100)

    [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + "shutters_test_2.xml", can_oversample = False)
    assert(oversampling == 1)


def test_parser_4():
    """
    Test failing if various properties are not specified.
    """
    for fname in ["shutters_test_3.xml", "shutters_test_4.xml", "shutters_test_5.xml", "shutters_test_6.xml"]:
        failed = False
        try:
            [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + fname)
        except xmlParser.ShutterXMLException as e:
            print(e)
            failed = True
    
        assert(failed)


def test_parser_5():
    """
    Test failing if various properties are out of range.
    """
    for fname in ["shutters_test_7.xml", "shutters_test_8.xml", "shutters_test_9.xml",
                  "shutters_test_10.xml", "shutters_test_11.xml", "shutters_test_12.xml"]:
        failed = False
        try:
            [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + fname)
        except xmlParser.ShutterXMLException as e:
            print(e)
            failed = True
    
        assert(failed)


def test_parser_6():
    """
    Test parsing a correctly formatted XML shutters file by name.
    """
    [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + "shutters_test_13.xml")

    # Make we got it right.
    assert(s_info.color_data[0] is None)    
    assert(s_info.color_data[1] == [255,0,0])
    assert(s_info.color_data[2] is None)
        
    assert(s_info.frames == 3)
    assert(oversampling == 2)
    assert(numpy.allclose(numpy.zeros(6), waveforms[0]))
    assert(numpy.allclose(numpy.array([0.0, 0.0, 1.0, 1.0, 0.0, 0.0]), waveforms[1]))
    assert(numpy.allclose(numpy.zeros(6), waveforms[2]))


def test_parser_7():
    """
    Test failing on invalid name.
    """
    try:
        [s_info, waveforms, oversampling] = xmlParser.parseShuttersXML(name_to_id, data_dir + "shutters_test_14.xml")
    except xmlParser.ShutterXMLException as e:
        print(e)
        return
    
    assert(False)
    

if (__name__ == "__main__"):
    test_parser_1()
    test_parser_2()
    test_parser_3()
    test_parser_4()
    test_parser_5()
    test_parser_6()
    test_parser_7()

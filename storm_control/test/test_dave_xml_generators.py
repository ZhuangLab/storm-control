#!/usr/bin/env python
"""
Test Dave XML generators.
"""
import os

import storm_control.test as test

import storm_control.dave.xml_generators.v1Generator as v1Generator


def test_v1_1():
    """
    This just tests that the XML file is created without crashing. The positions 
    file is the expected format, but with a few blank lines at the end to make
    it more interesting.
    """
    input_xml = test.daveXmlFilePathAndName("v1_generator_test.xml")
    input_positions = test.daveXmlFilePathAndName("v1_generator_test_positions.txt")
    output_xml = os.path.join(test.dataDirectory(), "dave_sequence.xml")

    v1Generator.generate(None, input_xml, input_positions, output_xml)


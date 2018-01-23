#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import distutils.cmd
import platform
import os
import setuptools.command.build_py
import subprocess
import sys

from setuptools import setup, find_packages


version = "2.0"
description = "STORM microscope control code."
long_description = ""

setup(
    name='storm_control',
    version=version,
    description=description,
    long_description=long_description,
    author='Hazen Babcock',
    author_email='hbabcock at fas.harvard.edu',
    url='https://github.com/ZhuangLab/storm-control',

    zip_safe=False,
    packages=find_packages(),

    package_data={},
    exclude_package_data={},
    include_package_data=True,

    requires=[],

    setup_requires=[],
    tests_require=[],
    
    license="",  
    keywords='storm,microscopy',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: MIT',
        'Programming Language :: C',
        'Programming Language :: Python :: 3',
    ],
)

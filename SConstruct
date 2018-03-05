#!/usr/bin/env python

import os
import platform

# Configure build environment.
env = None
if (platform.system() == 'Windows'):

    #
    # Check for user defined compiler.
    # i.e. > scons.bat -Q compiler=mingw
    #
    # The compiler needs to be in the users path.
    #
    compiler = ARGUMENTS.get('compiler', '')
    print("Using compiler", compiler)
    if (len(compiler) > 0):
        env = DefaultEnvironment(tools = [compiler],
                                 ENV = {'PATH' : os.environ['PATH'],
                                        'TMP' : os.environ['TMP'],
                                        'TEMP' : os.environ['TEMP']})
        
# Use the current environment if nothing was specified.
if env is None:
    env = Environment(ENV = os.environ)


# C compiler flags.
#
# FIXME: Visual C flags?
if (env['CC'] == "gcc"):
    if (platform.system() == 'Linux'):
        if True:
            env.Append(CCFLAGS = ['-O3','-Wall'],
                       LINKFLAGS = ['-Wl,-z,defs'])
        else: # Build with debugging.
            env.Append(CCFLAGS = ['-Og','-Wall'],
                       LINKFLAGS = ['-Wl,-z,defs'])
    else:
        env.Append(CCFLAGS = ['-O3','-Wall'])


# hal4000/halLib/c_image_manipulation.
if True:
    Default(env.SharedLibrary('./storm_control/c_libraries/c_image_manipulation',
                              ['./storm_control/hal4000/halLib/c_image_manipulation.c']))

# hal4000/focusLock/focus_quality.
if True:
    Default(env.SharedLibrary('./storm_control/c_libraries/focus_quality',
                              ['./storm_control/hal4000/focusLock/focus_quality.c']))

# hal4000/spotCounter/LMMoment.
if True:
    Default(env.SharedLibrary('./storm_control/c_libraries/LMMoment',
                              ['./storm_control/hal4000/spotCounter/LMMoment.c']))

    

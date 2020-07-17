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

# Library names and paths.
fftw_lib = 'fftw3'
fftw_lib_path = []

# Windows specific library settings.
if (platform.system() == 'Windows'):
    fftw_lib = 'fftw3-3'
    conf = Configure(env)
    if not conf.CheckLib(fftw_lib):
        print("FFTW3 library not found, using storm-control version.")
        fftw_lib_path = ['#/storm_control/c_libraries/']        


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

# sc_hardware/utility/corr_2d_gauss.
if True:
    Default(env.SharedLibrary('./storm_control/c_libraries/corr_2d_gauss',
                              ['./storm_control/sc_hardware/utility/corr_2d_gauss.c'],
                              LIBS = ['-lm']))

# sc_hardware/utility/af_lock.
if True:
    Default(env.SharedLibrary('./storm_control/c_libraries/af_lock',
                              ['./storm_control/sc_hardware/utility/af_lock.c'],
                              LIBS = [fftw_lib, '-lm'],
                              LIBPATH = fftw_lib_path, 
                              CPPPATH = fftw_lib_path))

# sc_hardware/pointGrey/spinshim.
#
# May need some adjustment depending on what library you have & your directory layout.
#
if False:
    spin_inc_path = "C:/Program Files/Point Grey Research/Spinnaker/include/spinc"
    spin_lib_path = "C:/Program Files/Point Grey Research/Spinnaker/bin64/vs2013"
    Default(env.SharedLibrary('./storm_control/c_libraries/spinshim',
                              ['./storm_control/sc_hardware/pointGrey/spinshim.c'],
                              LIBS = ["SpinnakerC_v120"],
                              LIBPATH = spin_lib_path,
                              CPPPATH = spin_inc_path))

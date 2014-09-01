# storm-control #
This is a repository of code developed in the [Zhuang Lab](http://zhuang.harvard.edu) for the acquisition of STORM movies.

# Installation #
You will need Python and PyQt as well as a number of other libraries. Please see the Install.txt file in the hal4000 folder.

# Directory Layout #
dave - This folder contains software (dave.py) that is used to control hal for automated acquisition of multiple images and/or STORM movies. Dave controls Hal via TCP/IP.

fluidics - This folder contains software (kilroy.py) to control a series of pumps and valves so that fluid control can be integrated with imaging. 

hal4000 - This folder contains the hal-4000 microscope control and image acquisition software (hal-4000.py).

sc_hardware - This folder contains classes for interfacing with various bits of hardware. Folders are (usually) the manufacturers name.

sc_library - This folder contains the modules that are used in multiple different programs.

steve - This folder contains software (steve.py) that is used to take and assemble image mosaics. This is useful for array tomography experiments, among other things. Steve also controls Hal via TCP/IP.

zee-calibrator - This folder contains software (main.py) that is used to generate calibration curves for astigmatism based 3D STORM imaging. Calibration data acquired using Hal needs to be analyzed by STORM image analysis software like Insight3 (available by request from the Zhuang Lab) or 3D-DAOSTORM before it can be processed using zee-calibrator.

# General notes #
1. This software is written primarily in Python with a few C helper libraries.

2. Doxygen documentation is available (for Dave, HAL and Steve), but you'll have to run doxygen to create it.

3. The different branches correspond to different setups. Ideally these are all modifications off the tip of master, but depending on update frequency some may lag a bit.

4. The software is provided "as is" in the hope that others might find it useful. While it is fairly stable and has been developed and used since 2009 in the Zhuang lab, we provide no gaurantee that any future changes that are made will maintain backwards compatibility with older versions.

5. We can only provide fairly limited support. You will probably have the most success adapting this software for your purposes if you are reasonably familiar with the Python programming language.

6. Questions should be addressed to Hazen Babcock (hbabcock _at_ fas.harvard.edu).


The Hal software controls the microscope.

Please see the INSTALL.txt file for instructions on how to 
get started. 

Please see the overview.txt file for a very high level overview 
of the organization of the Hal software.

As explained in the INSTALL.txt file, the software will initially 
run in emulation mode (i.e. it pretends that it is talking to a 
camera, stage, laser control system, etc.). To get it to control 
your specific hardware you should first come up with a unique name 
for your microscope, such as "myscope". You then have to create 
modules to control the hardware for your microscope, following the 
examples provided. Or, if the examples will work "as is" for your 
setup, then you can use them directly. Once you have your modules 
you need to create a file called "myscope_hardware.xml". This file 
specifies how to control the hardware attached to the setup. You 
will also need to create a file called "myscope_default.xml", to 
specify the default parameters to use when the program starts. 
Finally, to get HAL to load your setup instead of the default 
"none" setup you can specify a setup name, hardware and parameters
file at the command prompt as explained below.

Option 1: This run HAL in emulation mode.

> python hal-4000.py

Option 2: This will run an actual setup.

> python hal-4000.py storm3 xml\storm3_hardware.xml xml\storm3_default.xml

See also the .bat files that we use to start the software on our
setups.

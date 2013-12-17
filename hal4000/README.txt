
The Hal software controls the microscope.

The Dave and Steve programs depend on some libraries in the
halLib folder, so the hal4000 directory needs to be in your
Python path.

Please see the INSTALL.txt file for instructions on how to 
get started. 

Please see the overview.txt file for a very high level overview 
of the organization of the Hal software.

As explained in the INSTALL.txt file, the software will initially 
run in emulation mode (i.e. it pretends that it is talking to a 
camera, stage, laser control system, etc.). To get it to control 
your specific hardware you will first need to come up with a 
unique name for your microscope, such as "myscope". You then have 
to create files (classes) to control the hardware for your 
microscope, following the examples provided. For example, you will 
need to create (in the camera folder) a file for your camera called
"myscopeCamera.py", which can just be a copy of one of the existing
files (such as "storm3Camera.py"). Then to get Hal to load your
setup instead of the default "none" setup, you can change the
setup_name field in the settings_default.xml file.

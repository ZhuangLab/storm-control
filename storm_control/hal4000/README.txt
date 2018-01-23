
The Hal software controls the microscope.

Please see the INSTALL.txt file for instructions on how to 
get started. 

Please see the overview.txt file for a very high level overview 
of the organization of the Hal software.

As explained in the INSTALL.txt file, the software will initially 
run in emulation mode (i.e. it pretends that it is talking to a 
camera, stage, laser control system, etc.). To get it to control 
your specific hardware you will need to create a config.xml file
for it. Example configuration files are located in the
hal4000/xml directory.

Option 1: This runs HAL in emulation mode.

> python hal-4000.py xml/none_config.xml

Option 2: This will run an actual setup.

> python hal-4000.py xml/my_setup_config.xml

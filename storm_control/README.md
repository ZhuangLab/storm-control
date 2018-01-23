
## Directory Layout ##

dave - This folder contains software (dave.py) that is used to control hal for automated acquisition of multiple images and/or STORM movies. Dave controls Hal and Kilroy via TCP/IP.

fluidics - This folder contains software (kilroy.py) to control a series of pumps and valves so that fluid control can be integrated with imaging. 

hal4000 - This folder contains the hal-4000 microscope control and image acquisition software (hal-4000.py).

hazelnut - (Work in progress) This folder contains software (hazelnut.py) for transferring files from the acquisition computer to remote storage.

sc_hardware - This folder contains classes for interfacing with various bits of hardware. Folders are (usually) the manufacturers name.

sc_library - This folder contains the modules that are used in multiple different programs.

steve - This folder contains software (steve.py) that is used to take and assemble image mosaics. This is useful for array tomography experiments, among other things. Steve also controls Hal via TCP/IP.

test - Unit tests for this project.

zee_calibrator - (Deprecated) This folder contains software (main.py) that is used to generate calibration curves for astigmatism based 3D STORM imaging. Calibration data acquired using Hal needs to be analyzed by STORM image analysis software like Insight3 (available by request from the Zhuang Lab) or 3D-DAOSTORM before it can be processed using zee-calibrator.

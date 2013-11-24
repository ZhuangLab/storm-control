
The project layout:

 hal4000 - This folder contains the hal-4000 microscope control and
   image acquisition software (hal-4000.py).

 dave - This folder contains software (dave.py) that is used to 
   control hal for automated acquisition of multiple images and/or 
   STORM movies. Dave controls Hal via TCP/IP.

 steve - This folder contains software (steve.py) that is used to 
   take and assemble image mosaics. This is useful for array 
   tomography experiments, among other things. Steve also controls
   Hal via TCP/IP.

 zee-calibrator - This folder contains software (main.py) that
   is used to generate calibration curves for astigmatism based 
   3D STORM imaging. Calibration data acquired using Hal needs
   to be analyzed by STORM image analysis software like Insight3 
   (available by request from the Zhuang Lab) or 3D-DAOSTORM 
   before it can be processed using zee-calibrator.


General notes:

 1. This software is written primarily in Python with a few
    C helper libraries.

 2. Doxygen documentation is available.

 3. The software is provided "as is" in the hope that others
    might find it useful. While it is fairly stable and has been 
    developed and used since 2009 in the Zhuang lab, we provide 
    no gaurantee that any future changes that are made will 
    maintain backwards compatibility with older versions.

 4. We can only provide fairly limited support. You will
    probably have the most success adapting this software for
    your purposes if you are reasonably familiar with the Python 
    programming language.


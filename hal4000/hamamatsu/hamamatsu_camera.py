#!/usr/bin/python
#
# A ctypes based interface to Hamamatsu cameras.
# (tested on a sCMOS Flash 4.0).
#
# The documentation is a little confusing to me on this subject..
# I used c_int32 when this is explicitly specified, otherwise I use c_int.
#
# Hazen 09/13
#

import ctypes

# Some Hamamatsu constants.
DCAMERR_NOERROR = 1  # I made this one up. It seems to be the "good" result.

DCAM_IDSTR_MODEL = int("0x04000104",0)


#
# Check return value of the dcam function call.
# Throw an error if not as expected?
#
def checkStatus(fn_return, fn_name= ""):
    if (fn_return != DCAMERR_NOERROR):
        print " dcam:", fn_name, "returned", fn_return

# Initialization
dcam = ctypes.windll.dcamapi
temp = ctypes.c_int32(0)
checkStatus(dcam.dcam_init(None, ctypes.byref(temp), None), "dcam_init")
n_cameras = temp.value


#
# Functions.
#

def getModelInfo(camera_id):
    c_buf_len = 20
    c_buf = ctypes.create_string_buffer(c_buf_len)
    checkStatus(dcam.dcam_getmodelinfo(ctypes.c_int32(camera_id),
                                       ctypes.c_int32(DCAM_IDSTR_MODEL),
                                       c_buf,
                                       ctypes.c_int(c_buf_len)),
                "dcam_getmodelinfo")
    return c_buf.value


#
# Camera interface class.
#

class HamamatsuCamera():

    def __init__(self, camera_id):
        
        self.camera_id = camera_id
        self.camera_model = getModelInfo(camera_id)
        
        self.camera_handle = ctypes.c_int(0)
        checkStatus(dcam.dcam_open(ctypes.byref(self.camera_handle),
                                   ctypes.c_int32(self.camera_id),
                                   None),
                    "dcam_open")

    def getBinning(self):
        binning = ctypes.c_int32(0)
        checkStatus(dcam.dcam_getbinning(self.camera_handle,
                                         ctypes.byref(binning)),
                    "dcam_getbinning")
        return binning.value

    def shutdown(self):
        checkStatus(dcam.dcam_close(self.camera_handle),
                    "dcam_close")


#
# Testing.
#
if __name__ == "__main__":

    print "found:", n_cameras, "cameras"
    if (n_cameras > 0):
        print "camera 0 model:", getModelInfo(0)

        hcam = HamamatsuCamera(0)
        print "binning is:", hcam.getBinning()
        hcam.shutdown()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

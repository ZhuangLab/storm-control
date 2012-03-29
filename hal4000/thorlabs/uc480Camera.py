#!/usr/bin/python
#
# Captures pictures from a Thorlabs uc480 (software) series cameras.
#
# Hazen 03/12
#

import ctypes
import ctypes.util
import ctypes.wintypes
import numpy
from PIL import Image
import time

Handle = ctypes.wintypes.HANDLE

# some definitions
IS_AOI_IMAGE_GET_AOI = 0x0002
IS_AOI_IMAGE_SET_AOI = 0x0001
IS_DONT_WAIT = 0
IS_GET_STATUS = 0x8000
IS_SEQUENCE_CT = 2
IS_SET_CM_Y8 = 6
IS_SUCCESS = 0
IS_WAIT = 1

class CameraInfo(ctypes.Structure):
    _fields_ = [("SensorID", ctypes.wintypes.WORD),
                ("strSensorName", ctypes.c_char * 32),
                ("nColorMode", ctypes.c_char),
                ("nMaxWidth", ctypes.wintypes.DWORD),
                ("nMaxHeight", ctypes.wintypes.DWORD),
                ("bMasterGain", ctypes.wintypes.BOOL),
                ("bRGain", ctypes.wintypes.BOOL),
                ("bGGain", ctypes.wintypes.BOOL),
                ("bBGain", ctypes.wintypes.BOOL),
                ("bGlobShutter", ctypes.wintypes.BOOL),
                ("Reserved", ctypes.c_char * 16)]

class AOIRect(ctypes.Structure):
    _fields_ = [("s32X", ctypes.wintypes.INT),
                ("s32Y", ctypes.wintypes.INT),
                ("s32Width", ctypes.wintypes.INT),
                ("s32Height", ctypes.wintypes.INT)]

# load the DLL
#uc480_dll = ctypes.util.find_library('uc480')
#if uc480_dll is None:
#    print 'uc480.dll not found'

uc480 = ctypes.cdll.LoadLibrary("c:\windows\system32\uc480_64.dll")

# helper functions
def check(fn_return):
    if not (fn_return == IS_SUCCESS):
        print "uc480: Call failed with error", fn_return

# Camera Interface Class
class Camera(Handle):
    def __init__(self, camera_id = 0):
        Handle.__init__(self, 0)

        # Initialize camera.
        check(uc480.is_InitCamera(ctypes.byref(self), ctypes.wintypes.HWND(0)))

        # Get some information about the camera.
        self.info = CameraInfo()
        check(uc480.is_GetSensorInfo(self, ctypes.byref(self.info)))
        self.im_width = self.info.nMaxWidth
        self.im_height = self.info.nMaxHeight

        # Set camera to capture in BW.
        check(uc480.is_SetColorMode(self, IS_SET_CM_Y8))

        # Setup capture parameters.
        self.bitpixel = 8     # This is correct for a BW camera anyway..
        self.cur_frame = 0
        self.data = False
        self.id = 0
        self.image = False
        self.running = False
        self.setBuffers()

    def captureImage(self):
        check(uc480.is_FreezeVideo(self, IS_WAIT))
        return self.getImage()

    def getCameraStatus(self, status_code):
        return uc480.is_CameraStatus(self, status_code, IS_GET_STATUS)

    def getImage(self):
        check(uc480.is_CopyImageMem(self, self.image, self.id, self.data.ctypes.data))
        return self.data

    def getNextImage(self):
        while (self.cur_frame == self.getCameraStatus(IS_SEQUENCE_CT)):
            time.sleep(0.05)
        self.cur_frame += 1
        return self.getImage()

    def getSensorInfo(self):
        return self.info

    def setAOI(self, x_start, y_start, width, height):
        self.im_width = width
        self.im_height = height
        aoi_rect = AOIRect(x_start, y_start, width, height)
        check(uc480.is_AOI(self,
                           IS_AOI_IMAGE_SET_AOI,
                           ctypes.byref(aoi_rect),
                           ctypes.sizeof(aoi_rect)))
        self.setBuffers()

    def setBuffers(self):
        self.data = numpy.zeros((self.im_height, self.im_width), dtype = numpy.uint8)
        if self.image:
            check(uc480.is_FreeImageMem(self, self.image, self.id))
        self.image = ctypes.c_char_p()
        self.id = ctypes.c_int()
        check(uc480.is_AllocImageMem(self,
                                     ctypes.c_int(self.im_width),
                                     ctypes.c_int(self.im_height),
                                     ctypes.c_int(self.bitpixel),
                                     ctypes.byref(self.image),
                                     ctypes.byref(self.id)))
        check(uc480.is_SetImageMem(self, self.image, self.id))

    def setFrameRate(self, frame_rate = 1000, verbose = False):
        new_fps = ctypes.c_double()
        check(uc480.is_SetFrameRate(self,
                                    ctypes.c_double(frame_rate),
                                    ctypes.byref(new_fps)))
        if verbose:
            print "uc480: Set frame rate to", new_fps.value, "FPS"

    def shutDown(self):
        check(uc480.is_ExitCamera(self))

    def startCapture(self):
        check(uc480.is_CaptureVideo(self, IS_DONT_WAIT))

    def stopCapture(self):
        check(uc480.is_StopLiveVideo(self, IS_WAIT))

# QPD emulation class
class USBQPD():
    def __init__(self):
        self.image = None

        # open camera
        self.cam = Camera()

        # set camera AOI
        self.x_start = 836
        self.y_start = 434
        self.x_width = 300
        self.y_width = 300
        self.cam.setAOI(self.x_start,
                        self.y_start,
                        self.x_width,
                        self.y_width)

        # set camera to run as fast as possible
        self.cam.setFrameRate()

        self.X = numpy.arange(self.y_width) - 0.5*float(self.y_width)

    def capture(self):
        self.image = self.cam.captureImage()
        return self.image

    def getImage(self):
        return self.image

    def qpdScan(self):
        data = self.capture()
        data_ave = numpy.average(data, axis = 1)
        power = numpy.sum(data_ave)
        x_offset = numpy.sum(self.X * data_ave)
        return [power, x_offset, 0.0]

    def shutDown(self):
        self.cam.shutDown()

# Testing
if __name__ == "__main__":
    cam = Camera()
    reps = 50

    if 1:
        cam.setAOI(900, 500, 300, 300)
        cam.setFrameRate(verbose = True)
        image = cam.captureImage()
        im = Image.fromarray(image)
        im.save("temp.png")

    if 0:
        cam.startCapture()
        st = time.time()
        for i in range(reps):
            print i
            image = cam.getNextImage()
        print "time:", time.time() - st
        cam.stopCapture()

    if 0:
        cam.setAOI(100, 100, 200, 200)
        st = time.time()
        for i in range(reps):
            print i
            image = cam.captureImage()
        print "time:", time.time() - st

    cam.shutDown()

    #print image.shape, numpy.min(image), numpy.max(image)

    #im = Image.fromarray(image)
    #im.save("temp.png")
    #im.show()


# Bonus code section..

#    def setSize(self, width, height):
#        if (width > self.info.nMaxWidth) or (height > self.info.nMaxHeight):
#            print "uc480: Width of Height are too large"
#        else:
#            self.im_width = width
#            self.im_height = height
#            self.setBuffers()
        
#    def waitForImage(self, timeout = 100):
#        check(uc480.is_WaitForNextImage(self,
#                                        ctypes.wintypes.UINT(timeout),
#                                        ctypes.byref(self.image),
#                                        ctypes.byref(self.id)))


#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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

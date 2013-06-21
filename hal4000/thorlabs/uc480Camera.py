#!/usr/bin/python
#
# Captures pictures from a Thorlabs uc480 (software) series cameras.
#
# Hazen 02/13
#

import ctypes
import ctypes.util
import ctypes.wintypes
import numpy
import os
from PIL import Image
import platform
import scipy
import scipy.optimize
import time

Handle = ctypes.wintypes.HANDLE

# some definitions
IS_AOI_IMAGE_GET_AOI = 0x0002
IS_AOI_IMAGE_SET_AOI = 0x0001
IS_DONT_WAIT = 0
IS_ENABLE_ERR_REP = 1
IS_GET_STATUS = 0x8000
IS_IGNORE_PARAMETER = -1
IS_SEQUENCE_CT = 2
IS_SET_CM_Y8 = 6
IS_SET_GAINBOOST_OFF = 0x0000
IS_SUCCESS = 0
IS_TRIGGER_TIMEOUT = 0
IS_WAIT = 1

class CameraInfo(ctypes.Structure):
    _fields_ = [("CameraID", ctypes.wintypes.DWORD),
                ("DeviceID", ctypes.wintypes.DWORD),
                ("SensorID", ctypes.wintypes.DWORD),
                ("InUse", ctypes.wintypes.DWORD),
                ("SerNo", ctypes.c_char * 16),
                ("Model", ctypes.c_char * 16),
                ("Reserved", ctypes.wintypes.DWORD * 16)]

class CameraProperties(ctypes.Structure):
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

if (platform.architecture()[0] == "32bit"):
    uc480 = ctypes.cdll.LoadLibrary("c:\windows\system32\uc480.dll")
else:
    uc480 = ctypes.cdll.LoadLibrary("c:\windows\system32\uc480_64.dll")


# Helper functions
def check(fn_return, fn_name = ""):
    if not (fn_return == IS_SUCCESS):
        print "uc480: Call failed with error", fn_return, fn_name

def create_camera_list(num_cameras):
    class CameraList(ctypes.Structure):
        _fields_ = [("Count", ctypes.c_long),
                    ("Cameras", CameraInfo*num_cameras)]
    a_list = CameraList()
    a_list.Count = num_cameras
    return a_list


# Least squares gaussian fitting functions
def fitAFunctionLS(data, params, fn):
    result = params
    errorfunction = lambda p: numpy.ravel(fn(*p)(*numpy.indices(data.shape)) - data)
    good = True
    [result, cov_x, infodict, mesg, success] = scipy.optimize.leastsq(errorfunction, params, full_output = 1, maxfev = 500)
    if (success < 1) or (success > 4):
        print "Fitting problem:", mesg
        good = False
    return [result, good]

def symmetricGaussian(background, height, center_x, center_y, width):
    return lambda x,y: background + height*numpy.exp(-(((center_x-x)/width)**2 + ((center_y-y)/width)**2) * 2)

def fixedEllipticalGaussian(background, height, center_x, center_y, width_x, width_y):
    return lambda x,y: background + height*numpy.exp(-(((center_x-x)/width_x)**2 + ((center_y-y)/width_y)**2) * 2)

def fitSymmetricGaussian(data, sigma):
    params = [numpy.min(data),
              numpy.max(data),
              0.5 * data.shape[0],
              0.5 * data.shape[1],
              2.0 * sigma]
    return fitAFunctionLS(data, params, symmetricGaussian)

def fitFixedEllipticalGaussian(data, sigma):
    params = [numpy.min(data),
              numpy.max(data),
              0.5 * data.shape[0],
              0.5 * data.shape[1],
              2.0 * sigma,
              2.0 * sigma]
    return fitAFunctionLS(data, params, fixedEllipticalGaussian)


#
# UC480 Camera Interface Class
#
class Camera(Handle):
    def __init__(self, camera_id):
        Handle.__init__(self, camera_id)

        # Initialize camera.
        check(uc480.is_InitCamera(ctypes.byref(self), ctypes.wintypes.HWND(0)), "is_InitCamera")
        #check(uc480.is_SetErrorReport(self, IS_ENABLE_ERR_REP))

        # Get some information about the camera.
        self.info = CameraProperties()
        check(uc480.is_GetSensorInfo(self, ctypes.byref(self.info)), "is_GetSensorInfo")
        self.im_width = self.info.nMaxWidth
        self.im_height = self.info.nMaxHeight

        # Initialize some general camera settings.
        check(uc480.is_SetColorMode(self, IS_SET_CM_Y8), "is_SetColorMode")
        check(uc480.is_SetGainBoost(self, IS_SET_GAINBOOST_OFF), "is_SetGainBoost")
        check(uc480.is_SetGamma(self, 1), "is_SetGamma")
        check(uc480.is_SetHardwareGain(self,
                                       0,
                                       IS_IGNORE_PARAMETER,
                                       IS_IGNORE_PARAMETER,
                                       IS_IGNORE_PARAMETER),
              "is_SetHardwareGain")

        # Setup capture parameters.
        self.bitpixel = 8     # This is correct for a BW camera anyway..
        self.cur_frame = 0
        self.data = False
        self.id = 0
        self.image = False
        self.running = False
        self.setBuffers()

    def captureImage(self):
        check(uc480.is_FreezeVideo(self, IS_WAIT), "is_FreezeVideo")
        return self.getImage()

    def captureImageTest(self):
        check(uc480.is_FreezeVideo(self, IS_WAIT), "is_FreezeVideo")

    def getCameraStatus(self, status_code):
        return uc480.is_CameraStatus(self, status_code, IS_GET_STATUS, "is_CameraStatus")

    def getImage(self):
        check(uc480.is_CopyImageMem(self, self.image, self.id, self.data.ctypes.data), "is_CopyImageMem")
        return self.data

    def getNextImage(self):
        while (self.cur_frame == self.getCameraStatus(IS_SEQUENCE_CT)):
            time.sleep(0.05)
        self.cur_frame += 1
        return self.getImage()

    def getSensorInfo(self):
        return self.info

    def getTimeout(self):
        nMode = IS_TRIGGER_TIMEOUT
        pTimeout = ctypes.c_int(1)
        check(uc480.is_GetTimeout(self,
                                  ctypes.c_int(nMode),
                                  ctypes.byref(pTimeout)),
              "is_GetTimeout")
        return pTimeout.value

    def setAOI(self, x_start, y_start, width, height):
        # x and y start have to be multiples of 2.
        x_start = int(x_start/2)*2
        y_start = int(y_start/2)*2

        self.im_width = width
        self.im_height = height
        aoi_rect = AOIRect(x_start, y_start, width, height)
        check(uc480.is_AOI(self,
                           IS_AOI_IMAGE_SET_AOI,
                           ctypes.byref(aoi_rect),
                           ctypes.sizeof(aoi_rect)),
              "is_AOI")
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
                                     ctypes.byref(self.id)),
              "is_AllocImageMem")
        check(uc480.is_SetImageMem(self, self.image, self.id), "is_SetImageMem")

    def setFrameRate(self, frame_rate = 1000, verbose = False):
        new_fps = ctypes.c_double()
        check(uc480.is_SetFrameRate(self,
                                    ctypes.c_double(frame_rate),
                                    ctypes.byref(new_fps)),
              "is_SetFrameRate")
        if verbose:
            print "uc480: Set frame rate to", new_fps.value, "FPS"

    # 43MHz seems to be the max for this camera.
    def setPixelClock(self, pixel_clock_MHz = 40):
        check(uc480.is_SetPixelClock(self,
                                     ctypes.c_int(pixel_clock_MHz)))

    def setTimeout(self, timeout):
        nMode = IS_TRIGGER_TIMEOUT
        check(uc480.is_SetTimeout(self,
                                  ctypes.c_int(nMode),
                                  ctypes.c_int(timeout)),
              "is_SetTimeout")

    def shutDown(self):
        check(uc480.is_ExitCamera(self), "is_ExitCamera")

    def startCapture(self):
        check(uc480.is_CaptureVideo(self, IS_DONT_WAIT), "is_CaptureVideo")

    def stopCapture(self):
        check(uc480.is_StopLiveVideo(self, IS_WAIT), "is_StopLiveVideo")


#
# QPD emulation class.
#
# Default camera ROI of 200x200 pixels.
#
class CameraQPD():
    def __init__(self, camera_id = 1, fit_mutex = False):
        self.file_name = "cam_offsets_" + str(camera_id) + ".txt"
        self.fit_mode = 1
        self.fit_mutex = fit_mutex
        self.fit_size = 12
        self.image = None
        self.x_off1 = 0.0
        self.y_off1 = 0.0
        self.x_off2 = 0.0
        self.y_off2 = 0.0

        # Open camera
        self.cam = Camera(camera_id)

        # Set timeout
        self.cam.setTimeout(1)

        # Set camera AOI
        if (os.path.exists(self.file_name)):
            fp = open(self.file_name, "r")
            data = fp.readline().split(",")
            self.x_start = int(data[0])
            self.y_start = int(data[1])
            self.zero_dist = float(data[2])
            #[self.x_start, self.y_start, self.zero_dist] = map(int, fp.readline().split(","))
            fp.close()
        else:
            self.x_start = 646
            self.y_start = 216
            self.zero_dist = 100.0
        self.x_width = 200
        self.y_width = 200
        self.setAOI()

        # Set camera to run as fast as possible
        self.cam.setPixelClock()
        self.cam.setFrameRate()

        # Some derived parameters
        self.half_x = self.x_width/2
        self.half_y = self.y_width/2
        self.X = numpy.arange(self.y_width) - 0.5*float(self.y_width)

    def adjustAOI(self, dx, dy):
        self.x_start += dx
        self.y_start += dy
        if(self.x_start < 0):
            self.x_start = 0
        if(self.y_start < 0):
            self.y_start = 0
        if((self.x_start + self.x_width + 2) > self.cam.info.nMaxWidth):
            self.x_start = self.cam.info.nMaxWidth - (self.x_width + 2)
        if((self.y_start + self.y_width + 2) > self.cam.info.nMaxHeight):
            self.y_start = self.cam.info.nMaxHeight - (self.y_width + 2)
        self.setAOI()

    def adjustZeroDist(self, inc):
        self.zero_dist += inc

    def capture(self):
        self.image = self.cam.captureImage()
        return self.image

    def changeFitMode(self, mode):
        self.fit_mode = mode

    def fitGaussian(self, data):
        if (numpy.max(data) < 25):
            return [False, False, False, False]
        x_width = data.shape[0]
        y_width = data.shape[1]
        max_i = data.argmax()
        max_x = int(max_i/y_width)
        max_y = int(max_i%y_width)
        if (max_x > (self.fit_size-1)) and (max_x < (x_width - self.fit_size)) and (max_y > (self.fit_size-1)) and (max_y < (y_width - self.fit_size)):
            if self.fit_mutex:
                self.fit_mutex.lock()
            #[params, status] = fitSymmetricGaussian(data[max_x-self.fit_size:max_x+self.fit_size,max_y-self.fit_size:max_y+self.fit_size], 8.0)
            [params, status] = fitFixedEllipticalGaussian(data[max_x-self.fit_size:max_x+self.fit_size,max_y-self.fit_size:max_y+self.fit_size], 8.0)
            if self.fit_mutex:
                self.fit_mutex.unlock()
            params[2] -= self.fit_size/2
            params[3] -= self.fit_size/2
            return [max_x, max_y, params, status]
        else:
            return [False, False, False, False]

    def getImage(self):
        return [self.image, self.x_off1, self.y_off1, self.x_off2, self.y_off2]

    def getZeroDist(self):
        return self.zero_dist

    def qpdScan(self, reps = 4):
        power_total = 0.0
        offset_total = 0.0
        good_total = 0.0
        for i in range(reps):
            data = self.singleQpdScan()
            if (data[0] > 0):
                power_total += data[0]
                offset_total += data[1]
                good_total += 1.0
        if (good_total > 0):
            inv_good = 1.0/good_total
            return [power_total * inv_good, offset_total * inv_good, 0]
        else:
            return [0, 0, 0]

    def setAOI(self):
        self.cam.setAOI(self.x_start,
                        self.y_start,
                        self.x_width,
                        self.y_width)

    def shutDown(self):
        fp = open(self.file_name, "w")
        fp.write(str(self.x_start) + "," + str(self.y_start) + "," + str(self.zero_dist))
        fp.close()
        self.cam.shutDown()

    def singleQpdScan(self):
        data = self.capture().copy()
        power = numpy.max(data)

        if (power < 25):
            # This hack is because if you bombard the USB camera with 
            # update requests too frequently it will freeze. Or so I
            # believe, not sure if this is actually true.
            #
            # It still seems to freeze?
            time.sleep(0.05)
            return [0, 0, 0]

        # Determine offset by fitting gaussians to the two beam spots.
        # In the event that only beam spot can be fit then this will
        # attempt to compensate. However this assumes that the two
        # spots are centered across the mid-line of camera ROI.
        if (self.fit_mode == 1):
            dist1 = 0
            dist2 = 0
            self.x_off1 = 0.0
            self.y_off1 = 0.0
            self.x_off2 = 0.0
            self.y_off2 = 0.0

            # Fit first gaussian to data in the left half of the picture.
            total_good =0
            [max_x, max_y, params, status] = self.fitGaussian(data[:,:self.half_y])
            if status:
                total_good += 1
                self.x_off1 = float(max_x) + params[2] - self.half_x
                self.y_off1 = float(max_y) + params[3] - self.half_y
                dist1 = abs(self.y_off1)

            # Fit second gaussian to data in the right half of the picture.
            [max_x, max_y, params, status] = self.fitGaussian(data[:,-self.half_y:])
            if status:
                total_good += 1
                self.x_off2 = float(max_x) + params[2] - self.half_x
                self.y_off2 = float(max_y) + params[3]
                dist2 = abs(self.y_off2)

            if (total_good == 0):
                offset = 0
            elif (total_good == 1):
                offset = ((dist1 + dist2) - 0.5*self.zero_dist)*power
            else:
                offset = ((dist1 + dist2) - self.zero_dist)*power

            return [power, offset, 0]

        # Determine offset by moments calculation.
        else:
            self.x_off1 = 1.0e-6
            self.y_off1 = 0.0
            self.x_off2 = 1.0e-6
            self.y_off2 = 0.0

            total_good = 0
            data_band = data[self.half_x-15:self.half_x+15,:]

            # Moment for the object in the left half of the picture.
            x = numpy.arange(self.half_y)
            data_ave = numpy.average(data_band[:,:self.half_y], axis = 0)
            power1 = numpy.sum(data_ave)

            dist1 = 0.0
            if (power1 > 0.0):
                total_good += 1
                self.y_off1 = numpy.sum(x * data_ave) / power1 - self.half_y
                dist1 = abs(self.y_off1)

            # Moment for the object in the right half of the picture.
            data_ave = numpy.average(data_band[:,self.half_y:], axis = 0)
            power2 = numpy.sum(data_ave)

            dist2 = 0.0
            if (power2 > 0.0):
                total_good += 1
                self.y_off2 = numpy.sum(x * data_ave) / power2
                dist2 = abs(self.y_off2)

            if (total_good == 0):
                offset = 0
            elif (total_good == 1):
                offset = ((dist1 + dist2) - 0.5*self.zero_dist)*power
            else:
                offset = ((dist1 + dist2) - self.zero_dist)*power

            # The moment calculation is too fast. This is to slow things
            # down so that (hopefully) the camera doesn't freeze up.
            time.sleep(0.02)

            return [power, offset, 0]

#
# QPD emulation class with a 300x300 pixel ROI.
#
class CameraQPD300(CameraQPD):
    def __init__(self, camera_id = 1, fit_mutex = False):
        CameraQPD.__init__(self, camera_id, fit_mutex)

        # Change width to 300 x 300.
        self.x_width = 300
        self.y_width = 300
        self.setAOI()

        # Set camera to run as fast as possible
        self.cam.setPixelClock()
        self.cam.setFrameRate()
        
        # Some derived parameters
        self.half_x = self.x_width/2
        self.half_y = self.y_width/2
        self.X = numpy.arange(self.y_width) - 0.5*float(self.y_width)


# Testing
if __name__ == "__main__":
    cam = Camera(1)
    reps = 50

    if 0:
        cam.setAOI(772, 566, 200, 200)
        cam.setFrameRate(verbose = True)
        for i in range(100):
            print "start", i
            for j in range(100):
                image = cam.captureImage()
            print " stop"

        #im = Image.fromarray(image)
        #im.save("temp.png")

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

    if 1:
        for i in range(1):
            print i
            image = cam.captureImage()
            im = Image.fromarray(image)
            im.save("temp_" + str(i) + ".png")

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

#        # Determine number of cameras available.
#        c_num_cams = ctypes.wintypes.INT()
#        check(uc480.is_GetNumberOfCameras(ctypes.byref(c_num_cams)))
#        num_cams = int(c_num_cams.value)
#        # Initialize camera.
#        if(num_cams == 1):
#
#            check(uc480.is_InitCamera(ctypes.byref(self), ctypes.wintypes.HWND(0)))
#        else:
#            # We have to find the camera we want..
#            print "Found", num_cams, "cameras"
#            camera_data = create_camera_list(num_cams)
#            check(uc480.is_GetCameraList(ctypes.byref(camera_data)))
#            for camera in camera_data.Cameras:
#                print camera.SerNo, camera.CameraID, camera.DeviceID
#

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

#!/usr/bin/env python
"""
Captures pictures from a Thorlabs uc480 (software) series cameras.

FIXME: This only works with the uc480 Version 4.20 (or earlier) software.
       It will appear to work, then crash if you try and run it using
       ThorCam. If you install ThorCam you'll need to uninstall it
       first before installing the uc480 software. This software is
       available under the "Archive" tag in the ThorCam Software page.

Hazen 08/16
"""

import ctypes
import ctypes.util
import ctypes.wintypes
import numpy
import os

import time

import storm_control.sc_library.hdebug as hdebug

# import fitting libraries.
import storm_control.sc_hardware.utility.np_lock_peak_finder as npLPF

try:
    import storm_control.sc_hardware.utility.sa_lock_peak_finder as saLPF
except ModuleNotFoundError:
    pass

uc480 = None

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
    """
    The uc480 camera info structure.
    """
    _fields_ = [("CameraID", ctypes.wintypes.DWORD),
                ("DeviceID", ctypes.wintypes.DWORD),
                ("SensorID", ctypes.wintypes.DWORD),
                ("InUse", ctypes.wintypes.DWORD),
                ("SerNo", ctypes.c_char * 16),
                ("Model", ctypes.c_char * 16),
                ("Reserved", ctypes.wintypes.DWORD * 16)]

class CameraProperties(ctypes.Structure):
    """
    The uc480 camera properties structure.
    """
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
    """
    The uc480 camera AOI structure.
    """
    _fields_ = [("s32X", ctypes.wintypes.INT),
                ("s32Y", ctypes.wintypes.INT),
                ("s32Width", ctypes.wintypes.INT),
                ("s32Height", ctypes.wintypes.INT)]


# Helper functions

def check(fn_return, fn_name = ""):
    if not (fn_return == IS_SUCCESS):
        hdebug.logText("uc480: Call failed with error " + str(fn_return) + " " + fn_name)
        #print "uc480: Call failed with error", fn_return, fn_name

def create_camera_list(num_cameras):
    """
    Creates a empty CameraList structure.
    """
    class CameraList(ctypes.Structure):
        _fields_ = [("Count", ctypes.c_long),
                    ("Cameras", CameraInfo*num_cameras)]
    a_list = CameraList()
    a_list.Count = num_cameras
    return a_list

def loadDLL(dll_name):
    global uc480
    if uc480 is None:
        uc480 = ctypes.cdll.LoadLibrary(dll_name)


class Camera(Handle):
    """
    UC480 Camera Interface Class
    """
    def __init__(self, camera_id, ini_file = "uc480_settings.ini"):
        super().__init__(camera_id)

        # Initialize camera.
        check(uc480.is_InitCamera(ctypes.byref(self), ctypes.wintypes.HWND(0)), "is_InitCamera")
        #check(uc480.is_SetErrorReport(self, IS_ENABLE_ERR_REP))

        # Get some information about the camera.
        self.info = CameraProperties()
        check(uc480.is_GetSensorInfo(self, ctypes.byref(self.info)), "is_GetSensorInfo")
        self.im_width = self.info.nMaxWidth
        self.im_height = self.info.nMaxHeight

        # Initialize some general camera settings.
        if (os.path.exists(ini_file)):
            self.loadParameters(ini_file)
            hdebug.logText("uc480 loaded parameters file " + ini_file, to_console = False)
        else:
            check(uc480.is_SetColorMode(self, IS_SET_CM_Y8), "is_SetColorMode")
            check(uc480.is_SetGainBoost(self, IS_SET_GAINBOOST_OFF), "is_SetGainBoost")
            check(uc480.is_SetGamma(self, 1), "is_SetGamma")
            check(uc480.is_SetHardwareGain(self,
                                           0,
                                           IS_IGNORE_PARAMETER,
                                           IS_IGNORE_PARAMETER,
                                           IS_IGNORE_PARAMETER),
                  "is_SetHardwareGain")
            hdebug.logText("uc480 used default settings.", to_console = False)

        # Setup capture parameters.
        self.bitpixel = 8     # This is correct for a BW camera anyway..
        self.cur_frame = 0
        self.data = False
        self.id = 0
        self.image = False
        self.running = False
        self.setBuffers()

    def captureImage(self):
        """
        Wait for the next frame from the camera, then call self.getImage().
        """
        check(uc480.is_FreezeVideo(self, IS_WAIT), "is_FreezeVideo")
        return self.getImage()

    def captureImageTest(self):
        """
        For testing..
        """
        check(uc480.is_FreezeVideo(self, IS_WAIT), "is_FreezeVideo")

    def getCameraStatus(self, status_code):
        return uc480.is_CameraStatus(self, status_code, IS_GET_STATUS, "is_CameraStatus")

    def getImage(self):
        """
        Copy an image from the camera into self.data and return self.data
        """
        check(uc480.is_CopyImageMem(self, self.image, self.id, self.data.ctypes.data), "is_CopyImageMem")
        return self.data

    def getNextImage(self):
        """
        Waits until an image is available from the camera, then 
        call self.getImage() to return the new image.
        """
        print(self.cur_frame, self.getCameraStatus(IS_SEQUENCE_CT))
        while (self.cur_frame == self.getCameraStatus(IS_SEQUENCE_CT)):
            print("waiting..")
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

    def loadParameters(self, filename):
        check(uc480.is_LoadParameters(self,
                                      ctypes.c_char_p(filename.encode())))

    def saveParameters(self, filename):
        """
        Save the current camera settings to a file.
        """
        check(uc480.is_SaveParameters(self,
                                      ctypes.c_char_p(filename.encode())))

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
        """
        Based on the AOI, create the internal buffer that the camera will use and
        the intermediate buffer that we will copy the data from the camera into.
        """
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
            print("uc480: Set frame rate to {0:.1f} FPS".format(new_fps.value))

    def setPixelClock(self, pixel_clock_MHz):
        """
        43MHz seems to be the max for this camera?
        """
        check(uc480.is_SetPixelClock(self,
                                     ctypes.c_int(pixel_clock_MHz)))

    def setTimeout(self, timeout):
        nMode = IS_TRIGGER_TIMEOUT
        check(uc480.is_SetTimeout(self,
                                  ctypes.c_int(nMode),
                                  ctypes.c_int(timeout)),
              "is_SetTimeout")

    def shutDown(self):
        """
        Shut down the camera.
        """
        check(uc480.is_ExitCamera(self), "is_ExitCamera")

    def startCapture(self):
        """
        Start video capture (as opposed to single frame capture, which is done with self.captureImage().
        """
        check(uc480.is_CaptureVideo(self, IS_DONT_WAIT), "is_CaptureVideo")

    def stopCapture(self):
        """
        Stop video capture.
        """
        check(uc480.is_StopLiveVideo(self, IS_WAIT), "is_StopLiveVideo")


class CameraQPD(object):
    """
    QPD emulation class. The default camera ROI of 200x200 pixels.
    The focus lock is configured so that there are two laser spots on the camera.
    The distance between these spots is fit and the difference between this distance and the
    zero distance is returned as the focus lock offset. The maximum value of the camera
    pixels is returned as the focus lock sum.
    """
    def __init__(self,
                 allow_single_fits = False,
                 background = None,                 
                 camera_id = 1,
                 ini_file = None,
                 offset_file = None,
                 pixel_clock = None,
                 sigma = None,
                 x_width = None,
                 y_width = None,
                 **kwds):
        super().__init__(**kwds)

        self.allow_single_fits = allow_single_fits
        self.background = background
        self.fit_mode = 1
        self.fit_size = int(1.5 * sigma)
        self.image = None
        self.last_power = 0
        self.offset_file = offset_file
        self.sigma = sigma
        self.x_off1 = 0.0
        self.y_off1 = 0.0
        self.x_off2 = 0.0
        self.y_off2 = 0.0
        self.zero_dist = 0.5 * x_width

        # Add path information to files that should be in the same directory.
        ini_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ini_file)

        # Open camera
        self.cam = Camera(camera_id, ini_file = ini_file)

        # Set timeout
        self.cam.setTimeout(1)

        # Set camera AOI x_start, y_start.
        with open(self.offset_file) as fp:
            [self.x_start, self.y_start] = map(int, fp.readline().split(",")[:2])

        # Set camera AOI.
        self.x_width = x_width
        self.y_width = y_width
        self.setAOI()

        # Run at maximum speed.
        self.cam.setPixelClock(pixel_clock)
        self.cam.setFrameRate(verbose = True)

        # Some derived parameters
        self.half_x = int(self.x_width/2)
        self.half_y = int(self.y_width/2)
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
        """
        Get the next image from the camera.
        """
        self.image = self.cam.captureImage()
        return self.image

    def changeFitMode(self, mode):
        """
        mode 1 = gaussian fit, any other value = first moment calculation.
        """
        self.fit_mode = mode

    def doMoments(self, data):
        """
        Perform a moment based calculation of the distances.
        """
        self.x_off1 = 1.0e-6
        self.y_off1 = 0.0
        self.x_off2 = 1.0e-6
        self.y_off2 = 0.0

        total_good = 0
        data_band = data[self.half_y-15:self.half_y+15,:]

        # Moment for the object in the left half of the picture.
        x = numpy.arange(self.half_x)
        data_ave = numpy.average(data_band[:,:self.half_x], axis = 0)
        power1 = numpy.sum(data_ave)

        dist1 = 0.0
        if (power1 > 0.0):
            total_good += 1
            self.y_off1 = numpy.sum(x * data_ave) / power1 - self.half_x
            dist1 = abs(self.y_off1)

        # Moment for the object in the right half of the picture.
        data_ave = numpy.average(data_band[:,self.half_x:], axis = 0)
        power2 = numpy.sum(data_ave)

        dist2 = 0.0
        if (power2 > 0.0):
            total_good += 1
            self.y_off2 = numpy.sum(x * data_ave) / power2
            dist2 = abs(self.y_off2)

        # The moment calculation is too fast. This is to slow things
        # down so that (hopefully) the camera doesn't freeze up.
        time.sleep(0.02)
        
        return [total_good, dist1, dist2]

    def getImage(self):
        return [self.image, self.x_off1, self.y_off1, self.x_off2, self.y_off2, self.sigma]

    def getZeroDist(self):
        return self.zero_dist

    def qpdScan(self, reps = 4):
        """
        Returns sum and offset data from the camera in the 
        same format as what would be measured using a QPD.
        """
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
        """
        Set the camera AOI to current AOI.
        """
        self.cam.setAOI(self.x_start,
                        self.y_start,
                        self.x_width,
                        self.y_width)

    def shutDown(self):
        """
        Save the current camera AOI location and offset. Shutdown the camera.
        """
        if self.offset_file:
            with open(self.offset_file, "w") as fp:
                fp.write(str(self.x_start) + "," + str(self.y_start))
        self.cam.shutDown()

    def singleQpdScan(self):
        """
        Perform a single measurement of the focus lock offset and camera sum signal.
        """
        data = self.capture().copy()

        if (self.background > 0): # Toggle between sum signal calculations
            power = numpy.sum(data.astype(numpy.int64)) - self.background
        else:
            power = numpy.max(data)
        
        if (power < 25):
            #
            # This hack is because if you bombard the USB camera with 
            # update requests too frequently it will freeze. Or so I
            # believe, not sure if this is actually true.
            #
            # It still seems to freeze?
            #
            time.sleep(0.05)
            return [0, 0, 0]

        if (power == self.last_power):
            #
            # Or for reasons unclear it will keep returning the same
            # frame?
            #        
            #print("> UC480-QPD: Duplicate image detected!")
            time.sleep(0.1)
            return [0, 0, 0]

        self.last_power = power

        # Determine offset by fitting gaussians to the two beam spots.
        # In the event that only beam spot can be fit then this will
        # attempt to compensate. However this assumes that the two
        # spots are centered across the mid-line of camera ROI.
        if (self.fit_mode == 1):
            [total_good, dist1, dist2] = self.doFit(data)

        # Determine offset by moments calculation.
        else:
            [total_good, dist1, dist2] = self.doMoments(data)
                        
        # Calculate offset.
        if (total_good == 0):
            return [0, 0, 0]
        elif (total_good == 1):
            if self.allow_single_fits:
                offset = ((dist1 + dist2) - 0.5*self.zero_dist)
            else:
                return [0, 0, 0]
        else:
            offset = ((dist1 + dist2) - self.zero_dist)

        return [power, offset, 0]


class CameraQPDScipyFit(CameraQPD):
    """
    This version uses scipy to do the fitting.
    """
    def __init__(self, fit_mutex = False, **kwds):
        super().__init__(**kwds)

        self.fit_mutex = fit_mutex

    def doFit(self, data):
        dist1 = 0
        dist2 = 0
        self.x_off1 = 0.0
        self.y_off1 = 0.0
        self.x_off2 = 0.0
        self.y_off2 = 0.0

        # numpy finder/fitter.
        #
        # Fit first gaussian to data in the left half of the picture.
        total_good =0
        [max_x, max_y, params, status] = self.fitGaussian(data[:,:self.half_x])
        if status:
            total_good += 1
            self.x_off1 = float(max_x) + params[2] - self.half_y
            self.y_off1 = float(max_y) + params[3] - self.half_x
            dist1 = abs(self.y_off1)

        # Fit second gaussian to data in the right half of the picture.
        [max_x, max_y, params, status] = self.fitGaussian(data[:,-self.half_x:])
        if status:
            total_good += 1
            self.x_off2 = float(max_x) + params[2] - self.half_y
            self.y_off2 = float(max_y) + params[3]
            dist2 = abs(self.y_off2)

        return [total_good, dist1, dist2]
        
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
            #[params, status] = npLPF.fitSymmetricGaussian(data[max_x-self.fit_size:max_x+self.fit_size,max_y-self.fit_size:max_y+self.fit_size], 8.0)
            #[params, status] = npLPF.fitFixedEllipticalGaussian(data[max_x-self.fit_size:max_x+self.fit_size,max_y-self.fit_size:max_y+self.fit_size], 8.0)
            [params, status] = npLPF.fitFixedEllipticalGaussian(data[max_x-self.fit_size:max_x+self.fit_size,max_y-self.fit_size:max_y+self.fit_size], self.sigma)
            if self.fit_mutex:
                self.fit_mutex.unlock()
            params[2] -= self.fit_size
            params[3] -= self.fit_size
            return [max_x, max_y, params, status]
        else:
            return [False, False, False, False]


class CameraQPDSAFit(CameraQPD):
    """
    This version uses the storm-analysis project to do the fitting.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.fit_hl = None
        self.fit_hr = None

    def doFit(self, data):
        dist1 = 0
        dist2 = 0
        self.x_off1 = 0.0
        self.y_off1 = 0.0
        self.x_off2 = 0.0
        self.y_off2 = 0.0

        if self.fit_hl is None:
            self.fit_hl = saLPF.LockPeakFinder(offset = 5.0,
                                               sigma = self.sigma,
                                               threshold = 10)
            self.fit_hr = saLPF.LockPeakFinder(offset = 5.0,
                                               sigma = self.sigma,
                                               threshold = 10)

        total_good = 0
        [x1, y1, status] = self.fit_hl.findFitPeak(data[:,:self.half_x])
        if status:
            total_good += 1
            self.x_off1 = x1 - self.half_y
            self.y_off1 = y1 - self.half_x
            dist1 = abs(self.y_off1)
                
        [x2, y2, status] = self.fit_hr.findFitPeak(data[:,-self.half_x:])
        if status:
            total_good += 1
            self.x_off2 = x2 - self.half_y
            self.y_off2 = y2
            dist2 = abs(self.y_off2)

        return [total_good, dist1, dist2]

    def shutDown(self):
        super().shutDown()
        
        if self.fit_hl is not None:
            self.fit_hl.cleanup()
            self.fit_hr.cleanup()

        
# Testing
if (__name__ == "__main__"):

    from PIL import Image

    loadDLL("c:/windows/system32/uc480_64.dll")

    cam = Camera(1)
    reps = 200

    if False:
        cam.setAOI(772, 566, 200, 200)
        cam.setFrameRate(verbose = True)
        for i in range(100):
            print("start", i)
            for j in range(100):
                image = cam.captureImage()
            print(" stop")

        #im = Image.fromarray(image)
        #im.save("temp.png")

    if False:
        cam.setAOI(100, 100, 300, 300)
        cam.setPixelClock()
        cam.setFrameRate()
        cam.startCapture()
        st = time.time()
        for i in range(reps):
            #print i
            image = cam.getNextImage()
            #print i, numpy.sum(image)
        print("time:", time.time() - st)
        cam.stopCapture()

    if True:
        cam.setAOI(100, 100, 300, 300)
        cam.setPixelClock(25)
        cam.setFrameRate(verbose = True)
        st = time.time()
        print("starting")
        for i in range(reps):
            #print i
            image = cam.captureImage()
            #print(i, numpy.sum(image))
        print("{0:0d} frames in {1:.3f} seconds".format(reps, time.time() - st))

    if False:
        image = cam.captureImage()
        im = Image.fromarray(image)
        im.save("temp.png")
        cam.saveParameters("cam1.ini")

    cam.shutDown()

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

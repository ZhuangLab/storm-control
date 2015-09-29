#!/usr/bin/python
#
## @file
#
# Captures pictures from a Thorlabs uc480 (software) series cameras.
#
# NOTE: For reasons unclear, but perhaps due to a change in
#       ctypes, this module only works well with (64 bit) Python 
#       versions that are <= 2.7.8.
#
# Hazen 02/13
#

import ctypes
import ctypes.util
import ctypes.wintypes
import numpy
import os

import platform
import scipy
import scipy.optimize
import time

import sc_library.hdebug as hdebug

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

## CameraInfo
#
# The uc480 camera info structure.
#
class CameraInfo(ctypes.Structure):
    _fields_ = [("CameraID", ctypes.wintypes.DWORD),
                ("DeviceID", ctypes.wintypes.DWORD),
                ("SensorID", ctypes.wintypes.DWORD),
                ("InUse", ctypes.wintypes.DWORD),
                ("SerNo", ctypes.c_char * 16),
                ("Model", ctypes.c_char * 16),
                ("Reserved", ctypes.wintypes.DWORD * 16)]

## CameraProperties
#
# The uc480 camera properties structure.
#
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

## AOIRect
#
# The uc480 camera AOI structure.
#
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

## check
#
# @param fn_return The uc480 function return code.
# @param fn_name (Optional) The name of the function that was called, defaults to "".
#
def check(fn_return, fn_name = ""):
    if not (fn_return == IS_SUCCESS):
        hdebug.logText("uc480: Call failed with error " + str(fn_return) + " " + fn_name)
        #print "uc480: Call failed with error", fn_return, fn_name

## create_camera_list
#
# Creates a empty CameraList structure.
#
# @param num_cameras The number of cameras.
#
# @return A camera list structure.
#
def create_camera_list(num_cameras):
    class CameraList(ctypes.Structure):
        _fields_ = [("Count", ctypes.c_long),
                    ("Cameras", CameraInfo*num_cameras)]
    a_list = CameraList()
    a_list.Count = num_cameras
    return a_list


## fitAFunctionLS
#
# Does least squares fitting of a function.
#
# @param data The data to fit.
# @param params The initial values for the fit.
# @param fn The function to fit.
#
def fitAFunctionLS(data, params, fn):
    result = params
    errorfunction = lambda p: numpy.ravel(fn(*p)(*numpy.indices(data.shape)) - data)
    good = True
    [result, cov_x, infodict, mesg, success] = scipy.optimize.leastsq(errorfunction, params, full_output = 1, maxfev = 500)
    if (success < 1) or (success > 4):
        hdebug.logText("Fitting problem: " + mesg)
        #print "Fitting problem:", mesg
        good = False
    return [result, good]

## symmetricGaussian
#
# Returns a function that will return the amplitude of a symmetric 2D-gaussian at a given x, y point.
#
# @param background The gaussian's background.
# @param height The gaussian's height.
# @param center_x The gaussian's center in x.
# @param center_y The gaussian's center in y.
# @param width The gaussian's width.
#
# @return A function.
#
def symmetricGaussian(background, height, center_x, center_y, width):
    return lambda x,y: background + height*numpy.exp(-(((center_x-x)/width)**2 + ((center_y-y)/width)**2) * 2)

## fixedEllipticalGaussian
#
# Returns a function that will return the amplitude of a elliptical gaussian (constrained to be oriented
# along the XY axis) at a given x, y point.
#
# @param background The gaussian's background.
# @param height The gaussian's height.
# @param center_x The gaussian's center in x.
# @param center_y The gaussian's center in y.
# @param width_x The gaussian's width in x.
# @param width_y The gaussian's width in y.
#
# @return A function.
#
def fixedEllipticalGaussian(background, height, center_x, center_y, width_x, width_y):
    return lambda x,y: background + height*numpy.exp(-(((center_x-x)/width_x)**2 + ((center_y-y)/width_y)**2) * 2)

## fitSymmetricGaussian
#
# Fits a symmetric gaussian to the data.
#
# @param data The data to fit.
# @param sigma An initial value for the sigma of the gaussian.
#
# @return [[fit results], good (True/False)]
#
def fitSymmetricGaussian(data, sigma):
    params = [numpy.min(data),
              numpy.max(data),
              0.5 * data.shape[0],
              0.5 * data.shape[1],
              2.0 * sigma]
    return fitAFunctionLS(data, params, symmetricGaussian)

## fitFixedEllipticalGaussian
#
# Fits a fixed-axis elliptical gaussian to the data.
#
# @param data The data to fit.
# @param sigma An initial value for the sigma of the gaussian.
#
# @return [[fit results], good (True/False)]
#
def fitFixedEllipticalGaussian(data, sigma):
    params = [numpy.min(data),
              numpy.max(data),
              0.5 * data.shape[0],
              0.5 * data.shape[1],
              2.0 * sigma,
              2.0 * sigma]
    return fitAFunctionLS(data, params, fixedEllipticalGaussian)


## Camera
#
# UC480 Camera Interface Class
#
class Camera(Handle):

    ## __init__
    #
    # @param camera_id The identification number of the camera to connect to.
    # @param ini_file (Optional) A settings file to use to configure the camera, defaults to uc480_settings.ini.
    #
    def __init__(self, camera_id, ini_file = "uc480_settings.ini"):
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

    ## captureImage
    #
    # Wait for the next frame from the camera, then call self.getImage().
    #
    # @return An image (8 bit numpy array) from the camera.
    #
    def captureImage(self):
        check(uc480.is_FreezeVideo(self, IS_WAIT), "is_FreezeVideo")
        return self.getImage()

    ## captureImageTest
    #
    # For testing..
    def captureImageTest(self):
        check(uc480.is_FreezeVideo(self, IS_WAIT), "is_FreezeVideo")

    ## getCameraStatus
    #
    # @param status_code A status code.
    #
    # @return The camera status based on the status code.
    #
    def getCameraStatus(self, status_code):
        return uc480.is_CameraStatus(self, status_code, IS_GET_STATUS, "is_CameraStatus")

    ## getImage
    #
    # Copy an image from the camera into self.data and return self.data
    #
    # @return A 8 bit numpy array containing the data from the camera.
    #
    def getImage(self):
        check(uc480.is_CopyImageMem(self, self.image, self.id, self.data.ctypes.data), "is_CopyImageMem")
        return self.data

    ## getNextImage
    #
    # Waits until an image is available from the camera, then call self.getImage() to return the new image.
    #
    # @return The new image from the camera (as a 8 bit numpy array).
    #
    def getNextImage(self):
        print self.cur_frame, self.getCameraStatus(IS_SEQUENCE_CT)
        while (self.cur_frame == self.getCameraStatus(IS_SEQUENCE_CT)):
            print "waiting.."
            time.sleep(0.05)
        self.cur_frame += 1
        return self.getImage()

    ## getSensorInfo
    #
    # @return The camera properties structure for this camera.
    #
    def getSensorInfo(self):
        return self.info

    ## getTimeout
    #
    # @return The timeout value for the camera.
    #
    def getTimeout(self):
        nMode = IS_TRIGGER_TIMEOUT
        pTimeout = ctypes.c_int(1)
        check(uc480.is_GetTimeout(self,
                                  ctypes.c_int(nMode),
                                  ctypes.byref(pTimeout)),
              "is_GetTimeout")
        return pTimeout.value

    ## loadParameters
    #
    # @param file The file name of the camera parameters file to load.
    #
    def loadParameters(self, file):
        check(uc480.is_LoadParameters(self,
                                      ctypes.c_char_p(file)))

    ## saveParameters
    #
    # Save the current camera settings to a file.
    #
    # @param file The file name to save the settings in.
    #
    def saveParameters(self, file):
        check(uc480.is_SaveParameters(self,
                                      ctypes.c_char_p(file)))

    ## setAOI
    #
    # @param x_start The x pixel of the camera AOI.
    # @param y_start The y pixel of the camera AOI.
    # @param width The width in pixels of the AOI.
    # @param height The height in pixels of the AOI.
    #
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

    ## setBuffers
    #
    # Based on the AOI, create the internal buffer that the camera will use and
    # the intermediate buffer that we will copy the data from the camera into.
    #
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

    ## setFrameRate
    #
    # @param frame_rate (Optional) The desired frame rate in frames per second, defaults to 1000.
    # @param verbose (Optional) True/False, print the actual frame rate, defaults to False.
    #
    def setFrameRate(self, frame_rate = 1000, verbose = False):
        new_fps = ctypes.c_double()
        check(uc480.is_SetFrameRate(self,
                                    ctypes.c_double(frame_rate),
                                    ctypes.byref(new_fps)),
              "is_SetFrameRate")
        if verbose:
            print "uc480: Set frame rate to", new_fps.value, "FPS"

    ## setPixelClock
    #
    # 43MHz seems to be the max for this camera.
    #
    # @param pixel_clock_MHz (Optional) The desired pixel clock speed in MHz, defaults to 30.
    #
    def setPixelClock(self, pixel_clock_MHz = 30):
        check(uc480.is_SetPixelClock(self,
                                     ctypes.c_int(pixel_clock_MHz)))

    ## setTimeout
    #
    # @param timeout Set the camera time out.
    #
    def setTimeout(self, timeout):
        nMode = IS_TRIGGER_TIMEOUT
        check(uc480.is_SetTimeout(self,
                                  ctypes.c_int(nMode),
                                  ctypes.c_int(timeout)),
              "is_SetTimeout")

    ## shutDown
    #
    # Shut down the camera.
    #
    def shutDown(self):
        check(uc480.is_ExitCamera(self), "is_ExitCamera")

    ## startCapture
    #
    # Start video capture (as opposed to single frame capture, which is done with self.captureImage().
    #
    def startCapture(self):
        check(uc480.is_CaptureVideo(self, IS_DONT_WAIT), "is_CaptureVideo")

    ## stopCapture
    #
    # Stop video capture
    #
    def stopCapture(self):
        check(uc480.is_StopLiveVideo(self, IS_WAIT), "is_StopLiveVideo")


## CameraQPD
#
# QPD emulation class. The default camera ROI of 200x200 pixels.
# The focus lock is configured so that there are two laser spots on the camera.
# The distance between these spots is fit and the difference between this distance and the
# zero distance is returned as the focus lock offset. The maximum value of the camera
# pixels is returned as the focus lock sum.
#
class CameraQPD():

    ## __init__
    #
    # @param camera_id (Optional) The camera ID number, defaults to 1.
    # @param fit_mutex (Optional) A QMutex to use for fitting (to avoid thread safety issues with numpy), defaults to False.
    # @param x_width (Optional) AOI size in x, defaults to 200.
    # @param y_width (Optional) AOI size in y, defaults to 200.
    # @param sigma (Optional) Initial sigma for the fit, defaults to 8.0.
    #
    def __init__(self, camera_id = 1, fit_mutex = False, x_width = 200, y_width = 200, sigma = 8.0):
        self.file_name = "cam_offsets_" + str(camera_id) + ".txt"
        self.fit_mode = 1
        self.fit_mutex = fit_mutex
        self.fit_size = int(1.5 * sigma)
        self.image = None
        self.sigma = sigma
        self.x_off1 = 0.0
        self.y_off1 = 0.0
        self.x_off2 = 0.0
        self.y_off2 = 0.0
        self.zero_dist = 0.5 * x_width

        # Open camera
        self.cam = Camera(camera_id)

        # Set timeout
        self.cam.setTimeout(1)

        # Set camera AOI x_start, y_start.
        if (os.path.exists(self.file_name)):
            fp = open(self.file_name, "r")
            data = fp.readline().split(",")
            self.x_start = int(data[0])
            self.y_start = int(data[1])
            fp.close()
        else:
            self.x_start = 0
            self.y_start = 0

        # Set camera AOI.
        self.x_width = x_width
        self.y_width = y_width
        self.setAOI()

        # Run at maximum speed.
        self.cam.setPixelClock()
        self.cam.setFrameRate()

        # Some derived parameters
        self.half_x = self.x_width/2
        self.half_y = self.y_width/2
        self.X = numpy.arange(self.y_width) - 0.5*float(self.y_width)

    ## adjustAOI
    #
    # @param dx Amount to displace the AOI in pixels in x, needs to be a multiple of 2.
    # @param dy Amount to displace the AOI in pixels in y, needs to be a multiple of 2.
    #
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

    ## adjustZeroDist
    #
    # @param inc The amount to increment the zero distance value by.
    #
    def adjustZeroDist(self, inc):
        self.zero_dist += inc

    ## capture
    #
    # Get the next image from the camera.
    #
    def capture(self):
        self.image = self.cam.captureImage()
        return self.image

    ## changeFitMode
    #
    # @param mode 1 = gaussian fit, any other value = first moment calculation.
    #
    def changeFitMode(self, mode):
        self.fit_mode = mode

    ## fitGaussian
    #
    # @param data The data to fit a gaussian to.
    #
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
            #[params, status] = fitFixedEllipticalGaussian(data[max_x-self.fit_size:max_x+self.fit_size,max_y-self.fit_size:max_y+self.fit_size], 8.0)
            [params, status] = fitFixedEllipticalGaussian(data[max_x-self.fit_size:max_x+self.fit_size,max_y-self.fit_size:max_y+self.fit_size], self.sigma)
            if self.fit_mutex:
                self.fit_mutex.unlock()
            params[2] -= self.fit_size
            params[3] -= self.fit_size
            return [max_x, max_y, params, status]
        else:
            return [False, False, False, False]

    ## getImage
    #
    # @return [camera image, spot 1 x fit, spot 1 y fit, spot 2 x fit, spot 2 y fit]
    #
    def getImage(self):
        return [self.image, self.x_off1, self.y_off1, self.x_off2, self.y_off2, self.sigma]

    ## getZeroDist
    #
    # @return The distance between the spots that is considered to be zero offset.
    #
    def getZeroDist(self):
        return self.zero_dist

    ## qpdScan
    #
    # Returns sum and offset data from the camera in the same format as what would be measured using a QPD.
    #
    # @param reps (Optional) The number of measurements to average together, defaults to 4.
    #
    # @return [sum signal, x offset, 0].
    #
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

    ## setAOI
    #
    # Set the camera AOI to current AOI.
    #
    def setAOI(self):
        self.cam.setAOI(self.x_start,
                        self.y_start,
                        self.x_width,
                        self.y_width)

    ## shutDown
    #
    # Save the current camere AOI location and offset. Shutdown the camera.
    #
    def shutDown(self):
        fp = open(self.file_name, "w")
        #fp.write(str(self.x_start) + "," + str(self.y_start) + "," + str(self.zero_dist))
        fp.write(str(self.x_start) + "," + str(self.y_start))
        fp.close()
        self.cam.shutDown()

    ## singleQpdScan
    #
    # Perform a single measurement of the focus lock offset and camera sum signal.
    #
    # @return [sum, x-offset, y-offset].
    #
    def singleQpdScan(self):
        data = self.capture().copy()
        power = numpy.max(data)

        if (power < 25):
            # This hack is because if you bombard the USB camera with 
            # update requests too frequently it will freeze. Or so I
            # believe, not sure if this is actually true.
            #
            # It still seems to freeze?
            time.sleep(0.02)
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


# Testing
if __name__ == "__main__":

    from PIL import Image

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
        cam.setAOI(100, 100, 300, 300)
        cam.setPixelClock()
        cam.setFrameRate()
        cam.startCapture()
        st = time.time()
        for i in range(reps):
            #print i
            image = cam.getNextImage()
            #print i, numpy.sum(image)
        print "time:", time.time() - st
        cam.stopCapture()

    if 0:
        cam.setAOI(100, 100, 300, 300)
        cam.setPixelClock()
        cam.setFrameRate()
        st = time.time()
        for i in range(reps):
            #print i
            image = cam.captureImage()
            print i, numpy.sum(image)
        print "time:", time.time() - st

    if 1:
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

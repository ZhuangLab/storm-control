#!/usr/bin/env python
"""
A ctypes based interface to the Photometrics PVCAM library.

Hazen 10/17
"""
import ctypes
import numpy
import sys
import time

import sc_library.halExceptions as halExceptions
import sc_hardware.photometrics.pvcam_constants as pvc

pvcam = None

def check(value, fn_name = "??"):
    """
    Wrap all calls to pvcam with this to get any error messages.
    """
    if (value == 0):

        # Get the error message from the PVCAM library.
        error_msg = ctypes.c_char_p(' ' * pvc.ERROR_MSG_LEN)
        pvcam.pl_error_message(pvcam.pl_error_code(), error_msg)

        # Compose error message.
        error_message = fn_name + " failed with message: " + error_msg.value

        # Raise exception.
        raise PVCAMException(error_message)
        
        return False
    else:
        return True

def getCameraNames():
    """
    Return a list of all the available cameras.
    """
    # Query to get the total number of cameras.
    n_cams = pvc.int16()
    check(pvcam.pl_cam_get_total(ctypes.byref(n_cams)), "pl_cam_get_total")

    # Query the camera names.
    cam_name = ctypes.c_char_p(' ' * pvc.CAM_NAME_LEN)
    camera_names = []
    for i in range(n_cams.value):
        check(pvcam.pl_cam_get_name(pvc.int16(i), cam_name), "pl_cam_get_name")
        camera_names.append(cam_name.value)

    return camera_names

def initPVCAM():
    """
    Initialize the library.
    """
    check(pvcam.pl_pvcam_init(), "pl_pvcam_init")

def loadPVCAMDLL(pvcam_library_name):
    """
    Load the pvcam DLL.
    """
    global pvcam
    if pvcam is None:
        pvcam = ctypes.WinDLL(pvcam_library_name)

# Callback for receiving EOF events from the PVCAM library.
PVCAM_EOF_FUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.POINTER(pvc.FRAME_INFO), cypes.POINTER(pvc.uns32))

def py_eof_callback(c_frame_info, c_counter):
    print("eof_callback", c_counter[0], c_frame_info.contents.FrameNr)
    c_counter[0] += 1
    return 0

eof_callback = PVCAM_EOF_FUNC(py_eof_callback)

def uninitPVCAM():
    """
    Closes the library.
    """
    check(pvcam.pl_pvcam_uninit(), "pl_pvcam_uninit")


class PVCAMException(halExceptions.HardwareException):
    pass


class PVCAMCamera(object):
    """
    Python interface to a PVCAM camera.

    The basic idea is that we are going to keep track of how many frames the
    camera has acquired using an EOF callback. Then when HAL polls with getFrames()
    we'll return all the frames that have been acquired since the last polling.
    """
    def __init__(self, camera_name = None, **kwds):
        super(PVCAMCamera, self).__init__(**kwds)

        self.buffer_len = None
        self.data_buffer = None
        self.frame_size = None
        self.frame_x = None
        self.frame_y = None
        self.n_captured = pvc.uns32(0) # No more than 4 billion frames in a single capture..
        self.n_processed = 0

        # Open camera.
        c_name = ctypes.c_char_p(camera_name)
        self.hcam = pvc.int16(0)
        check(pvcam.pl_cam_open(c_name,
                                ctypes.byref(self.hcam),
                                pvc.int16(0)),
              "pl_cam_open")

        # Register our EOF callback. This callback is supposed to increment
        # self.n_captured every time the camera acquires a new frame.
        #
        check(pvcam.pl_cam_register_callback_ex3(self.hcam,
                                                 pvc.int32(pvc.PL_CALLBACK_EOF),
                                                 eof_callback,
                                                 ctypes.byref(self.n_captured)),
              "pl_cam_register_callback_ex3")

    def captureSetup(self, x_start, x_end, x_bin, y_start, y_end, y_bin, exposure_time):
        """
        Configure for image capture (circular buffer).

        The camera is zero indexed.

        exposure_time is in milliseconds by default?

        How to determine the number of frames per second at a given exposure 
        time? HAL will need to know this in order to time other things properly.
        """
        self.frame_x = (x_end - x_start)/x_bin
        self.frame_y = (y_end - y_start)/y_bin
        
        # Setup acquisition & determine how large a frame is (in pixels).
        frame_size = pvc.uns32(0)
        region = pvc.rgn_type(x_start, x_end, x_bin, y_start, y_end, y_bin)
        check(pvcam.pl_exp_setup_cont(self.hcam,
                                      pvc.uns16(1),
                                      ctypes.byref(region),
                                      pvc.int16(pvc.TIMED_MODE),
                                      pvc.uns32(exposure_time),
                                      cytpes.byref(frame_size),
                                      pvc.int16(pvc.CIRC_OVERWRITE)),
              "pl_exp_setup_cont")

        # This assumes that we are dealing with a 16 bit camera.
        # We should verify that it is the same self.frame_x * self.frame_y?
        #
        self.frame_size = frame_size.value/2

        # Allocate storage for the frames. For now we'll just allocate storage
        # for 100 frames, but it would be better to have this depend on the
        # exposure time (i.e. enough frames to buffer 2 seconds or something).
        #
        # Note: The PVCAM library limits the maximum buffer size to 2**32 bytes.
        #
        self.buffer_len = 100
        size = self.buffer_len * self.frame_size
        self.data_buffer = numpy.ascontiguousarray(numpy.empty(size, dtype = numpy.uint16))

    def getFrames(self):
        frames = []

        # Check if we have not gotten too far behind.
        if ((self.n_captured.value - self.n_processed) >= self.buffer_len):
            raise PVCAMException("PVCam buffer overflow.")
        
        # Get all the images that are currently available.
        #
        # Note: We are copying the images out of the buffer into (temporary)
        #       storage. Instead we could just create images that pointed
        #       to the buffer memory. However we decided not to do this as
        #       we don't have a good way to know when HAL is done processing
        #       the image.
        #
        while (self.n_processed < self.n_captured.value):
            print(self.n_processed, self.n_captured.value, self.buffer_len, self.frame_size)
            index = self.n_processed % self.buffer_len
            start = index * self.frame_size
            end = (index + 1) * self.frame_size
            frames.append(PVCAMFrameData(np_array = numpy.copy(self.data_buffer[start:end])))
            self.n_processed += 1

        return [frames, [self.frame_x, self.frame_y]]
        
    def getParam(self, pid, value, attrib):
        """
        Wrapper of pl_get_params, primarily for internal use.
        """

        # Overwrite whatever value is for some attributes.
        #
        if (attrib == pvc.ATTR_ACCESS):
            value = pvc.uns16()
        elif (attrib == pvc.ATTR_AVAIL):
            value = pvc.rs_bool()
        elif (attrib == pvc.ATTR_COUNT):
            value = pvc.uns32()
        elif (attrib == pvc.ATTR_TYPE):
            value = pvc.int16()
            
        check(pvcam.pl_get_param(self.hcam,
                                 pid,
                                 pvc.int16(attrib),
                                 ctypes.byref(value)),
              "pl_get_param")
        return value.value
    
    def getParameter(self, pname):
        """
        Returns the current value of a parameter.

        pname - The parameters ID or name.
        """
        pid = self.nameToID(pname)
        ptype = self.getParameterType(pid)

        # Get value for numbers.
        value = self.getTypeInstance(ptype)
        if value is not None:
            return self.getParam(pid, value, pvc.ATTR_CURRENT)

        # Get value for strings.
        if (ptype == pvc.TYPE_CHAR_PTR):
            # Get the string.
            count = self.getParameterCount(pid)
            cstring = ctypes.c_char_p(' ' * count)
            check(pvcam.pl_get_param(self.hcam,
                                     pid,
                                     pvc.int16(pvc.ATTR_CURRENT),
                                     cstring),
                  "pl_get_param")
            return cstring.value        

        raise PVCAMException("getParameter: unsupported type " + str(ptype))
    
    def getParameterCount(self, pname):
        """
        Return the number of values available for a parameter.
        """
        pid = self.nameToID(pname)
        return self.getParam(pid, None, pvc.ATTR_COUNT)
    
    def getParameterEnum(self, pname, pindex = None):
        """
        Returns value and description for an enumerated type.
        """
        pid = self.nameToID(pname)
        ptype = self.getParameterType(pid)
        pvalue = pvc.int32()

        # Verify that this is an enumerated type.
        if (ptype != pvc.TYPE_ENUM):
            raise PVCAMException("getParameterEnum: " + str(ptype) + " is not an enumerated type.")

        # Use current index if not specified.
        if pindex is None:
            cindex = pvc.uns32(pvc.ATTR_CURRENT)
        else:
            cindex = pvc.uns32(pindex)
            
        # Create string to store results.
        maxlen = 100
        cstring = ctypes.c_char_p(' ' * maxlen)
        
        check(pvcam.pl_get_enum_param(self.hcam,
                                      pid,
                                      cindex,
                                      ctypes.byref(pvalue),
                                      cstring,
                                      pvc.uns32(maxlen)),
              "pl_get_enum_param")

        return [pvalue.value, cstring.value]

    def getParameterMax(self, pname):
        """
        Return the maximum value for a parameter.
        """
        pid = self.nameToID(pname)
        ptype = self.getParameterType(pid)

        # Get value for numbers.
        value = self.getTypeInstance(ptype)
        if value is not None:
            return self.getParam(pid, value, pvc.ATTR_MAX)

        raise PVCAMException("getParameterMax: maximum not avaialable for " + str(ptype))

    def getParameterMin(self, pname):
        """
        Return the minimum value for a parameter.
        """
        pid = self.nameToID(pname)
        ptype = self.getParameterType(pid)

        # Get value for numbers.
        value = self.getTypeInstance(ptype)
        if value is not None:
            return self.getParam(pid, value, pvc.ATTR_MIN)

        raise PVCAMException("getParameterMin: minimum not avaialable for " + str(ptype))

    def getParameterType(self, pid):
        """
        Get the type of a parameter.
        """
        self.getParam(pid, None, pvc.ATTR_TYPE)

    def getTypeInstance(self, ptype):
        """
        Return a ctypes instance of ptype.
        """
        if (ptype == pvc.TYPE_INT16):
            return pvc.int16()
        elif (ptype == pvc.TYPE_INT32):
            return pvc.int32()
        elif (ptype == pvc.TYPE_FLT64):
            return pvc.flt64()
        elif (ptype == pvc.TYPE_UNS8):
            return pvc.uns8()
        elif (ptype == pvc.TYPE_UNS16):
            return pvc.uns16()
        elif (ptype == pvc.TYPE_UNS32):
            return pvc.uns32()
        elif (ptype == pvc.TYPE_UNS64):
            return pvc.uns64()
        elif (ptype == pvc.TYPE_ENUM):
            return pvc.int32()
        elif (ptype == pvc.TYPE_BOOLEAN):
            return pvc.rs_bool()
        elif (ptype == pvc.TYPE_INT8):
            return pvc.int8()
        
    def hasParameter(self, pname):
        """
        Check if the camera supports this parameter.
        """
        pid = self.nameToID(pname)
        avail = self.getParam(pid, None, pvc.ATTR_AVAIL)
        return not (avail.value == 0)

    def nameToID(self, pname):
        
        # If this is a name then we need to look it up.
        if not isinstance(pname, int):
            try:
                return pvc.uns32(getattr(pvc, pname.upper()))
            except AttributeError:
                raise PVCAMException("Unknown parameter " + str(pname))

        # Otherwise we assume that it is already an ID.
        else:
            return pvc.uns32(pname)

    def setParameter(self, pname, pvalue):
        """
        Set parameter pname to pvalue.
        """
        pid = self.nameToId(pname)
        ptype = self.getParameterType(pid)

        # Set parameter for numbers.
        value = self.getTypeInstance(ptype)
        if value is not None:
            value.value = pvalue            
            check(pvcam.pl_set_param(self.hcam,
                                     pid,
                                     ctypes.byref(value)),
                  "pl_set_param")
            return

        # Set parameter for string.
        if (ptype == pvc.TYPE_CHAR_PTR):
            # Special handling for strings.
            enc_string = pvalue.encode('ascii')
            check(pvcam.pl_set_param(self.hcam,
                                     pid,
                                     cytpes.create_string_buffer(enc_string)),
                  "pl_set_param")
            return

        raise PVCAMException("setParameter: unsupported type " + str(ptype))

    def shutdown(self):
        check(pvcam.pl_cam_deregister_callback(self.hcam,
                                               pvc.int32(pvc.PL_CALLBACK_EOF)),
              "pl_cam_deregister_callback")
        check(pvcam.pl_cam_close(self.hcam), "pl_cam_close")

    def startAcquisition(self):
        # Reset the acquisition counters.
        self.n_captured.value = 0
        self.n_processed = 0

        # Start the acquisition.
        check(pvcam.pl_exp_start_cont(self.hcam,
                                      self.data_buffer.ctypes.data,
                                      pvc.uns32(2*self.data_buffer.size)),
              "pl_exp_start_cont")

    def stopAcquisition(self):
        """
        Stop the current acquisition and tell the camera to go to the idle state.
        """
        check(pvcam.pl_exp_stop_cont(self.hcam,
                                     pvc.int16(pvc.CCS_HALT)),
              "pl_exp_stop_cont")


class PVCAMFrameData(object):
    """
    Store PVCAM frame data in a HAL friendly format. 

    By now you'd think we'd have a generic base class for this..
    """
    def __init__(self, np_array = None, **kwds):
        super(PVCAMFrameData, self).__init__(**kwds)
        
        self.np_array = np_array

    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data
    

if (__name__ == "__main__"):
    loadPVCAMDLL("c:\Windows\System32\pvcam64.dll")

    initPVCAM()

    # Get camera names.
    name = getCameraNames()

    # Get the first camera.
    cam = PVCAMCamera(camera_name = name[0])

    # Test getting some parameters.
    for param in ["param_temp", "param_pix_par_size", "param_shtr_status",
                  "param_readout_time", "param_bit_depth", "param_chip_name"]:
        print("Parameter: ", param)
        if cam.hasParameter(param):
            print("  value = ", cam.getParameter(param))
        else:
            print("  not available.")

    # Test querying the number of ports and readout speeds.
    print("querying ports and speeds.")
    n_ports = cam.getParameterCount("param_readout_port")
    for i in range(n_ports):
        [value, desc] = cam.getParameterEnum("param_readout_port", i)
        print("value = ", value, "desc = ", desc)
        cam.setParameter("param_readout_port", value)
        n_speeds = cam.getParameterMax("param_spdtab_index")
        for j in range(n_speeds):
            cam.setParameter("param_spd_tab_index", j)
            for param in ["param_bit_depth", "param_pix_time", "param_gain_index"]:
                print("  ", i, j, param, "=", cam.getParameter(param))
    
    # Configure acquisition, 512 x 512, 100ms exposure.
    cam.captureSetup(0, 511, 1, 0, 511, 1, 100)
    
    # Test repeated acquisition.
    for i in range(2):

        # Start / stop acquisition.
        cam.startAcquisition()
        time.sleep(1.0)
        cam.stopAcquisition()

        # See if we can get the frames that were acquired.
        [frames, shape] = cam.getFrames()
        for i, frame in enumerate(frames):
            print(frame.getData()[0:3])
    
    # Close the camera.
    cam.shutdown()

    uninitPVCAM()

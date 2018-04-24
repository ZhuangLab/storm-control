#!/usr/bin/env python
"""
A ctypes based interface to the Photometrics PVCAM library.

Hazen 10/17
"""
import ctypes
import numpy
import sys

import storm_control.sc_library.halExceptions as halExceptions
import storm_control.sc_hardware.photometrics.pvcam_constants as pvc

pvcam = None

def check(value, fn_name = "??"):
    """
    Wrap all calls to pvcam with this to get any error messages.
    """
    if (value == 0):

        # Get the error message from the PVCAM library.
        error_msg = ctypes.c_char_p((' ' * pvc.ERROR_MSG_LEN).encode())
        pvcam.pl_error_message(pvcam.pl_error_code(), error_msg)

        # Compose error message.
        error_message = fn_name + " failed with message: " + error_msg.value.decode()

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
    cam_name = ctypes.c_char_p((' ' * pvc.CAM_NAME_LEN).encode())
    camera_names = []
    for i in range(n_cams.value):
        check(pvcam.pl_cam_get_name(pvc.int16(i), cam_name), "pl_cam_get_name")
        camera_names.append(cam_name.value.decode("ascii"))

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
PVCAM_EOF_FUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.POINTER(pvc.FRAME_INFO), ctypes.POINTER(pvc.uns32))

def py_eof_callback(c_frame_info, c_counter):
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
        super().__init__(**kwds)

        self.buffer_len = None
        self.data_buffer = None
        self.frame_bytes = None
        self.frame_x = None
        self.frame_y = None
        self.n_captured = pvc.uns32(0) # No more than 4 billion frames in a single capture..
        self.n_processed = 0

        # Open camera.
        c_name = ctypes.c_char_p(camera_name.encode())
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
        self.frame_x = int((x_end - x_start + 1)/x_bin)
        self.frame_y = int((y_end - y_start + 1)/y_bin)
        
        # Setup acquisition & determine how large a frame is (in pixels).
        frame_size = pvc.uns32(0)
        region = pvc.rgn_type(x_start, x_end, x_bin, y_start, y_end, y_bin)
        check(pvcam.pl_exp_setup_cont(self.hcam,
                                      pvc.uns16(1),
                                      ctypes.byref(region),
                                      pvc.int16(pvc.TIMED_MODE),
                                      pvc.uns32(exposure_time),
                                      ctypes.byref(frame_size),
                                      pvc.int16(pvc.CIRC_OVERWRITE)),
              "pl_exp_setup_cont")

        # Store frame size in bytes.
        #
        self.frame_bytes = frame_size.value

        # Allocate storage for the frames. Use PVCAM's recommendation for the size.
        #
        size = self.getParameterDefault("param_frame_buffer_size")
        self.data_buffer = numpy.ascontiguousarray(numpy.zeros(size, dtype = numpy.uint8))
        self.buffer_len = int(size/self.frame_bytes)

    def getFrames(self):
        frames = []

        # Check if we have not gotten too far behind.
        if ((self.n_captured.value - self.n_processed) >= self.buffer_len):
            raise PVCAMException("PVCam buffer overflow.")

        # Get all the images that are currently available. Starting with the
        # oldest first. You have to call 'pl_exp_unlock_oldest_frame' because
        # otherwise you'll just get the same frame over and over again..
        # 
        while (self.n_processed < self.n_captured.value):
            data_ptr = ctypes.c_void_p()
            check(pvcam.pl_exp_get_oldest_frame(self.hcam,
                                                ctypes.byref(data_ptr)),
                  "pl_exp_get_oldest_frame")

            pv_data = PVCAMFrameData(self.frame_bytes)
            pv_data.copyData(data_ptr)
            frames.append(pv_data)
            
            check(pvcam.pl_exp_unlock_oldest_frame(self.hcam),
                  "pl_exp_unlock_oldest_frame")

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
    
    def getParameter(self, pname, attr_type):
        """
        Returns the current value of a parameter.

        pname - The parameters ID or name.
        """
        pid = self.nameToID(pname)
        ptype = self.getParameterType(pid)

        # Get value for numbers.
        value = self.getTypeInstance(ptype)
        if value is not None:
            return self.getParam(pid, value, attr_type)

        # Get value for strings.
        if (ptype == pvc.TYPE_CHAR_PTR):
            # Get the string.
            count = self.getParameterCount(pname)            
            cstring = ctypes.c_char_p((' ' * count).encode())
            check(pvcam.pl_get_param(self.hcam,
                                     pid,
                                     pvc.int16(attr_type),
                                     cstring),
                  "pl_get_param")
            return cstring.value.decode()

        raise PVCAMException("getParameter: unsupported type " + str(ptype))
    
    def getParameterCount(self, pname):
        """
        Return the number of values available for a parameter.
        """
        pid = self.nameToID(pname)
        return self.getParam(pid, None, pvc.ATTR_COUNT)
    
    def getParameterCurrent(self, pname):
        """
        Return the current value for a parameter.
        """
        return self.getParameter(pname, pvc.ATTR_CURRENT)
    
    def getParameterDefault(self, pname):
        """
        Return the default value for a parameter.
        """
        return self.getParameter(pname, pvc.ATTR_DEFAULT)
    
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
        cstring = ctypes.c_char_p((' ' * maxlen).encode())
        
        check(pvcam.pl_get_enum_param(self.hcam,
                                      pid,
                                      cindex,
                                      ctypes.byref(pvalue),
                                      cstring,
                                      pvc.uns32(maxlen)),
              "pl_get_enum_param")

        return [pvalue.value, cstring.value.decode()]

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
        return self.getParam(pid, None, pvc.ATTR_TYPE)

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
            return pvc.ulong64()
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
        return not (avail == 0)

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
        pid = self.nameToID(pname)
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
                                      pvc.uns32(self.data_buffer.size)),
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
    def __init__(self, size = None, **kwds):
        """
        Create a data object of the appropriate size.
        """
        super().__init__(**kwds)
        self.np_array = numpy.ascontiguousarray(numpy.empty(int(size/2), dtype=numpy.uint16))
        self.size = size

    def copyData(self, address):
        """
        Uses the C memmove function to copy data from an address in memory
        into memory allocated for the numpy array of this object.
        """
        ctypes.memmove(self.np_array.ctypes.data, address, self.size)
        
    def getData(self):
        return self.np_array

    def getDataPtr(self):
        return self.np_array.ctypes.data
    

if (__name__ == "__main__"):
    import tifffile
    import time

    loadPVCAMDLL("c:\Windows\System32\pvcam64.dll")

    initPVCAM()

    # Get camera names.
    names = getCameraNames()
    print("Camera names", ",".join(names))

    # Get the first camera.
    cam = PVCAMCamera(camera_name = names[0])

    # Test getting some parameters.
    if False:
        for param in ["param_temp", "param_pix_par_size", "param_shtr_status",
                      "param_readout_time", "param_bit_depth", "param_chip_name"]:
            print("Parameter: ", param)
            if cam.hasParameter(param):
                print("  value = ", cam.getParameterCurrent(param))
            else:
                print("  not available.")

    # Test querying the number of ports and readout speeds.
    if True:
        print("querying ports and speeds.")
        n_ports = cam.getParameterCount("param_readout_port")
        print("Number of ports", n_ports)
        for i in range(n_ports):
            [value, desc] = cam.getParameterEnum("param_readout_port", i)
            print("value = ", value, "desc = ", desc)
            cam.setParameter("param_readout_port", value)
            n_speeds = cam.getParameterCount("param_spdtab_index")
            print("  Number of speeds", n_speeds)
            for j in range(n_speeds):
                print("    speed", j)
                cam.setParameter("param_spdtab_index", j)
                for param in ["param_bit_depth", "param_pix_time", "param_gain_index"]:
                    print("      ", i, j, param, "=", cam.getParameterCurrent(param))

    # Test querying speed / bit depth.
    if False:
        print("Number of speeds", cam.getParameterCount("param_spdtab_index"))
        print("Number bit depths", cam.getParameterCount("param_bit_depth"))
    
    # Test querying exposure.
    if False:
        print(cam.getParameterCount("param_exp_res"), cam.getParameterCurrent("param_exp_res"))
        print(cam.getParameterCurrent("param_expose_out_mode"))
        print(cam.getParameterCurrent("param_metadata_enabled"))

    # Test acquisition.
    if False:

        x_size = 1024
        y_size = 1024
        
        # Configure acquisition, x_size by y_size, X millisecond exposure.
        cam.captureSetup(0, x_size - 1, 1, 0, y_size - 1, 1, 100)

        tf = tifffile.TiffWriter("capture.tif")
        
        # Test acquisition.
        for i in range(1):

            # Start acquisition.
            print("Starting camera.")
            cam.startAcquisition()

            for j in range(1):
                time.sleep(2.0)
                print("query", j)
            
                # See if we can get the frames that were acquired.
                [frames, shape] = cam.getFrames()
                for k, frame in enumerate(frames):
                    print(k, frame.getData()[0:3])
                    tf.save(frame.getData().reshape((x_size, y_size)))

            # Stop acquisition.
            print("Stopping camera.")
            cam.stopAcquisition()
            
            # See if we can get the frames that were acquired.
            [frames, shape] = cam.getFrames()
            for j, frame in enumerate(frames):
                print(j, frame.getData()[0:3])
                tf.save(frame.getData().reshape((x_size, y_size)))

        tf.close()
        
    # Close the camera.
    cam.shutdown()

    uninitPVCAM()

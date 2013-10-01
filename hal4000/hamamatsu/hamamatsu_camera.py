#!/usr/bin/python
#
# A ctypes based interface to Hamamatsu cameras.
# (tested on a sCMOS Flash 4.0).
#
# The documentation is a little confusing to me on this subject..
# I used c_int32 when this is explicitly specified, otherwise I use c_int.
#
# FIXME: I'm using the "old" functions because these are documented..
#    Switch to the "new" functions at some point.
#
# Hazen 09/13
#

import ctypes

# Hamamatsu constants.
DCAMCAP_EVENT_FRAMEREADY = int("0x0002", 0)

DCAMERR_NOERROR = 1  # I made this one up. It seems to be the "good" result.

DCAMPROP_ATTR_HASVALUETEXT = int("0x10000000", 0)

DCAMPROP_OPTION_NEAREST = int("0x80000000", 0)
DCAMPROP_OPTION_NEXT = int("0x01000000", 0)
DCAMPROP_OPTION_SUPPORT = int("0x00000000", 0)

DCAMPROP_TYPE_MODE = int("0x00000001", 0)
DCAMPROP_TYPE_LONG = int("0x00000002", 0)
DCAMPROP_TYPE_REAL = int("0x00000003", 0)
DCAMPROP_TYPE_MASK = int("0x0000000F", 0)

DCAMWAIT_TIMEOUT_INFINITE = int("0x80000000", 0)

DCAM_CAPTUREMODE_SNAP = 0
DCAM_CAPTUREMODE_SEQUENCE = 1

DCAM_DEFAULT_ARG = 0

DCAM_IDPROP_EXPOSURETIME = int("0x001F0110", 0)

DCAM_IDSTR_MODEL = int("0x04000104", 0)

# Hamamatsu structures.
class DCAM_PARAM_PROPERTYATTR(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int32),
                ("iProp", ctypes.c_int32),
                ("option", ctypes.c_int32),
                ("iReserved1", ctypes.c_int32),
                ("attribute", ctypes.c_int32),
                ("iGroup", ctypes.c_int32),
                ("iUnit", ctypes.c_int32),
                ("attribute2", ctypes.c_int32),
                ("valuemin", ctypes.c_double),
                ("valuemax", ctypes.c_double),
                ("valuestep", ctypes.c_double),
                ("valuedefault", ctypes.c_double),
                ("nMaxChannel", ctypes.c_int32),
                ("iReserved3", ctypes.c_int32),
                ("nMaxView", ctypes.c_int32),
                ("iProp_NumberOfElement", ctypes.c_int32),
                ("iProp_ArrayBase", ctypes.c_int32),
                ("iPropStep_Element", ctypes.c_int32)]

class DCAM_PARAM_PROPERTYVALUETEXT(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int32),
                ("iProp", ctypes.c_int32),
                ("value", ctypes.c_double),
                ("text", ctypes.c_char_p),
                ("textbytes", ctypes.c_int32)]

#
# Check return value of the dcam function call.
# Throw an error if not as expected?
#
def checkStatus(fn_return, fn_name= "unknown"):
    if (fn_return != DCAMERR_NOERROR):
        print " dcam:", fn_name, "returned", fn_return
    return fn_return

# Initialization
dcam = ctypes.windll.dcamapi
temp = ctypes.c_int32(0)
checkStatus(dcam.dcam_init(None, ctypes.byref(temp), None), 
            "dcam_init")
n_cameras = temp.value


#
# Functions.
#

def convertPropertyName(p_name):
    return p_name.lower().replace(" ", "_")

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

        self.buffer_index = 0
        self.camera_id = camera_id
        self.camera_model = getModelInfo(camera_id)
        self.frame_bytes = 0
        self.frame_x = 0
        self.frame_y = 0
        self.properties = {}
        self.number_image_buffers = 0

        # Open the camera.
        self.camera_handle = ctypes.c_void_p(0)
        checkStatus(dcam.dcam_open(ctypes.byref(self.camera_handle),
                                   ctypes.c_int32(self.camera_id),
                                   None),
                    "dcam_open")

        # Get camera properties.
        self.properties = self.getCameraProperties()

#    def getBinning(self):
#        binning = ctypes.c_int32(0)
#        checkStatus(dcam.dcam_getbinning(self.camera_handle,
#                                         ctypes.byref(binning)),
#                    "dcam_getbinning")
#        return binning.value

    # Return the ids & names of all the properties that the camera supports.
    def getCameraProperties(self):
        c_buf_len = 64
        c_buf = ctypes.create_string_buffer(c_buf_len)
        properties = {}
        prop_id = ctypes.c_int32(0)

        # Reset to the start.
        ret = dcam.dcam_getnextpropertyid(self.camera_handle,
                                          ctypes.byref(prop_id),
                                          ctypes.c_int32(DCAMPROP_OPTION_NEAREST))
        if (ret > 1):
            checkStatus(ret, "dcam_getnextpropertyid")

        # Get the first property.
        ret = dcam.dcam_getnextpropertyid(self.camera_handle,
                                          ctypes.byref(prop_id),
                                          ctypes.c_int32(DCAMPROP_OPTION_NEXT))
        if (ret > 1):
            checkStatus(ret, "dcam_getnextpropertyid")
        checkStatus(dcam.dcam_getpropertyname(self.camera_handle,
                                              prop_id,
                                              c_buf,
                                              ctypes.c_int32(c_buf_len)),
                    "dcam_getpropertyname")

        # Get the rest of the properties.
        last = -1
        while (prop_id.value != last):
            last = prop_id.value
            properties[convertPropertyName(c_buf.value)] = prop_id.value
            ret = dcam.dcam_getnextpropertyid(self.camera_handle,
                                              ctypes.byref(prop_id),
                                              ctypes.c_int32(DCAMPROP_OPTION_NEXT))
            if (ret > 1):
                checkStatus(ret, "dcam_getnextpropertyid")
            checkStatus(dcam.dcam_getpropertyname(self.camera_handle,
                                                  prop_id,
                                                  c_buf,
                                                  ctypes.c_int32(c_buf_len)),
                        "dcam_getpropertyname")
        return properties

    # Gets all of the available frames.
    #
    # This will block waiting for new frames even if 
    # there new frames available when it is called.
    def getFrames(self):

        # Wait for a new frame.
        dwait = ctypes.c_int(DCAMCAP_EVENT_FRAMEREADY)
        checkStatus(dcam.dcam_wait(self.camera_handle,
                                   ctypes.byref(dwait),
                                   ctypes.c_int(DCAMWAIT_TIMEOUT_INFINITE),
                                   None),
                    "dcam_wait")

        # Check how many new frames there are.
        b_index = ctypes.c_int32(0)
        f_count = ctypes.c_int32(0)          
        checkStatus(dcam.dcam_gettransferinfo(self.camera_handle,
                                              ctypes.byref(b_index),
                                              ctypes.byref(f_count)),
                    "dcam_gettransferinfo")

        cur_buffer_index = b_index.value
        print self.buffer_index, cur_buffer_index

        # Determine which frames to get.
        to_get = []
        if (cur_buffer_index < self.buffer_index):
            for i in range(self.buffer_index + 1, self.number_image_buffers):
                to_get.append(i)
            for i in range(cur_buffer_index + 1):
                to_get.append(i)
        else:
            for i in range(self.buffer_index, cur_buffer_index):
                to_get.append(i+1)
        self.buffer_index = cur_buffer_index

        # Get the frames.
        print to_get
        
    # Return the list of camera properties.
    def getProperties(self):
        return self.properties

    # Return the attribute structure of a particular property.
    #
    # FIXME (OPTIMIZATION): Keep track of known attributes?
    #
    def getPropertyAttribute(self, property_name):
        p_attr = DCAM_PARAM_PROPERTYATTR()
        p_attr.cbSize = ctypes.sizeof(p_attr)
        p_attr.iProp = self.properties[property_name]
        ret = checkStatus(dcam.dcam_getpropertyattr(self.camera_handle,
                                                    ctypes.byref(p_attr)),
                          "dcam_getpropertyattr")
        if (ret == 0):
            print " property", property_id, "is not supported"
            return False
        else:
            return p_attr

    # Return the text options of a property (if any).
    def getPropertyText(self, property_name):
        prop_attr = self.getPropertyAttribute(property_name)
        if not (prop_attr.attribute & DCAMPROP_ATTR_HASVALUETEXT):
            return {}
        else:
            # Create property text structure.
            prop_id = self.properties[property_name]
            v = ctypes.c_double(prop_attr.valuemin)

            prop_text = DCAM_PARAM_PROPERTYVALUETEXT()
            c_buf_len = 64
            c_buf = ctypes.create_string_buffer(c_buf_len)
            #prop_text.text = ctypes.c_char_p(ctypes.addressof(c_buf))
            prop_text.cbSize = ctypes.c_int32(ctypes.sizeof(prop_text))
            prop_text.iProp = ctypes.c_int32(prop_id)
            prop_text.value = v
            prop_text.text = ctypes.addressof(c_buf)
            prop_text.textbytes = c_buf_len

            # Collect text options.
            done = False
            text_options = {}
            while not done:
                # Get text of current value.
                checkStatus(dcam.dcam_getpropertyvaluetext(self.camera_handle, 
                                                       ctypes.byref(prop_text)),
                            "dcam_getpropertyvaluetext")
                text_options[prop_text.text] = int(v.value)

                # Get next value.
                ret = dcam.dcam_querypropertyvalue(self.camera_handle,
                                                   ctypes.c_int32(prop_id),
                                                   ctypes.byref(v),
                                                   ctypes.c_int32(DCAMPROP_OPTION_NEXT))
                prop_text.value = v
                if (ret == 0):
                    done = True

            return text_options

    # Return the range for an attribute.
    def getPropertyRange(self, property_name):
        prop_attr = self.getPropertyAttribute(property_name)
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_REAL):
            return [float(prop_attr.valuemin), float(prop_attr.valuemax)]
        else:
            return [int(prop_attr.valuemin), int(prop_attr.valuemax)]
    
    # Return the current setting of a particular property.
    def getPropertyValue(self, property_name):

        # Check if the property exists.
        if not (property_name in self.properties):
            print " unknown property name:", property_name
            return False
        prop_id = self.properties[property_name]

        # Get the property attributes.
        prop_attr = self.getPropertyAttribute(property_name)

        # Get the property value.
        c_value = ctypes.c_double(0)
        checkStatus(dcam.dcam_getpropertyvalue(self.camera_handle,
                                               ctypes.c_int32(prop_id),
                                               ctypes.byref(c_value)),
                    "dcam_getpropertyvalue")

        # Convert type based on attribute type.
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_MODE):
            prop_type = "MODE"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_LONG):
            prop_type = "LONG"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_REAL):
            prop_type = "REAL"
            prop_value = c_value.value
        else:
            prop_type = "NONE"
            prop_value = False
    
        return [prop_value, prop_type]

    # Set the value of a property.
    def setPropertyValue(self, property_name, property_value):

        # Check if the property exists.
        if not (property_name in self.properties):
            print " unknown property name:", property_name
            return False

        # If the value is text, figure out what the 
        # corresponding numerical property value is.
        if (type(property_value) == type("")):
            text_values = self.getPropertyText(property_name)
            if (property_value in text_values):
                property_value = float(text_values[property_value])
            else:
                print " unknown property text value:", property_value, "for", property_name
                return False
        
        # Check that the property is within range.
        [pv_min, pv_max] = self.getPropertyRange(property_name)
        if (property_value < pv_min):
            print " property value is less than minimum:", property_value, pv_min
            property_value = pv_min
        if (property_value > pv_max):
            print " property value is greater than maximum:", property_value, pv_max
            property_value = pv_max
        
        # Set the property value, return what it was set too.
        prop_id = self.properties[property_name]
        p_value = ctypes.c_double(property_value)
        checkStatus(dcam.dcam_setgetpropertyvalue(self.camera_handle,
                                                  ctypes.c_int32(prop_id),
                                                  ctypes.byref(p_value),
                                                  ctypes.c_int32(DCAM_DEFAULT_ARG)),
                    "dcam_setgetpropertyvalue")
        return p_value.value

    # Start data acquisition.
    def startAcquistion(self):
        self.buffer_index = -1

        # Get frame properties.
        self.frame_bytes = self.getPropertyValue("buffer_framebytes")[0]
        self.frame_x = self.getPropertyValue("subarray_hsize")[0]
        self.frame_y = self.getPropertyValue("subarray_vsize")[0]

        # Set capture mode.
        checkStatus(dcam.dcam_precapture(self.camera_handle,
                                         ctypes.c_int(DCAM_CAPTUREMODE_SEQUENCE)),
                    "dcam_precapture")

        # Allocate image buffers.
        self.number_image_buffers = 10
        checkStatus(dcam.dcam_allocframe(self.camera_handle,
                                         ctypes.c_int32(self.number_image_buffers)),
                    "dcam_allocframe")

        # Start acquisition.
        checkStatus(dcam.dcam_capture(self.camera_handle),
                    "dcam_capture")

    # Stop data acquisition.
    def stopAcquistion(self):

        # Stop acquisition.
        checkStatus(dcam.dcam_idle(self.camera_handle),
                    "dcam_idle")

        # Free image buffers.
        self.number_image_buffers = 0
        checkStatus(dcam.dcam_freeframe(self.camera_handle),
                    "dcam_freeframe")

    # Close down the connection to the camera.
    def shutdown(self):
        checkStatus(dcam.dcam_close(self.camera_handle),
                    "dcam_close")


#
# Testing. 
# 
# This prints out all of the available properties of the camera.
#
if __name__ == "__main__":

    import time

    print "found:", n_cameras, "cameras"
    if (n_cameras > 0):
        print "camera 0 model:", getModelInfo(0)

        hcam = HamamatsuCamera(0)

        # List support properties.
        if 0:
            print "Supported properties:"
            props = hcam.getProperties()
            for i, id_name in enumerate(sorted(props.keys())):
                [p_value, p_type] = hcam.getPropertyValue(id_name)
                print "  ", i, ")", id_name, " = ", p_value, " type is:", p_type
                text_values = hcam.getPropertyText(id_name)
                if (len(text_values) > 0):
                    print "          option / value"
                    for t_val in text_values:
                        print "         ", t_val[1], "/", t_val[0]

        # Test image capture.
        if 1:
            print hcam.setPropertyValue("defect_correct_mode", "OFF")
            hcam.startAcquistion()
            for i in range(20):
                time.sleep(0.05)
                hcam.getFrames()
            hcam.stopAcquistion()

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

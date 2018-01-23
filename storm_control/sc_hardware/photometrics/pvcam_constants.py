#!/usr/bin/env python
# -*- coding: utf-8
#
# Copyright 2017 Mick Phillips (mick.phillips@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""pvcam library wrapper.

This module exposes pvcam C library functions in python.

TODO: support camera metadata.
"""

##
#
# Some modifications to work in the storm-control project.
#
# Hazen 10/17
#

import ctypes
import numpy

# Readout transform mapping - {CHIP_NAME: {port: transform}}
READOUT_TRANSFORMS = {
    'Evolve-5': {0: (0,0,0),
                 1: (1,0,0)}
}

# === Data types ===
# Base typedefs, from pvcam SDK master.h
#typedef unsigned short rs_bool;
rs_bool = ctypes.c_ushort
#typedef signed char    int8;
int8 = ctypes.c_byte
#typedef unsigned char  uns8;
uns8 = ctypes.c_ubyte
#typedef short          int16;
int16 = ctypes.c_short
#typedef unsigned short uns16;
uns16 = ctypes.c_ushort
#typedef int            int32;
int32 = ctypes.c_int32
#typedef unsigned int   uns32;
uns32 = ctypes.c_uint32
#typedef float          flt32;
flt32 = ctypes.c_float
#typedef double         flt64;
flt64 = ctypes.c_double
#typedef unsigned long long ulong64;
ulong64 = ctypes.c_ulonglong
#typedef signed long long long64;
long64 = ctypes.c_longlong
# enums
enumtype = ctypes.c_int32


# defines, typedefs and enums parsed from pvcam.h .
MAX_CAM = 16
CAM_NAME_LEN = 32
PARAM_NAME_LEN = 32
ERROR_MSG_LEN = 255
CCD_NAME_LEN = 17
MAX_ALPHA_SER_NUM_LEN = 32
MAX_PP_NAME_LEN = 32
MAX_SYSTEM_NAME_LEN = 32
MAX_VENDOR_NAME_LEN = 32
MAX_PRODUCT_NAME_LEN = 32
MAX_CAM_PART_NUM_LEN = 32
MAX_GAIN_NAME_LEN = 32
OPEN_EXCLUSIVE = 0
NORMAL_COOL = 0
CRYO_COOL = 1
MPP_UNKNOWN = 0
MPP_ALWAYS_OFF = 1
MPP_ALWAYS_ON = 2
MPP_SELECTABLE = 3
SHTR_FAULT = 0
SHTR_OPENING = 1
SHTR_OPEN = 2
SHTR_CLOSING = 3
SHTR_CLOSED = 4
SHTR_UNKNOWN = 5
PMODE_NORMAL = 0
PMODE_FT = 1
PMODE_MPP = 2
PMODE_FT_MPP = 3
PMODE_ALT_NORMAL = 4
PMODE_ALT_FT = 5
PMODE_ALT_MPP = 6
PMODE_ALT_FT_MPP = 7
COLOR_NONE = 0
COLOR_RESERVED = 1
COLOR_RGGB = 2
COLOR_GRBG = 3
COLOR_GBRG = 4
COLOR_BGGR = 5
ATTR_CURRENT = 0
ATTR_COUNT = 1
ATTR_TYPE = 2
ATTR_MIN = 3
ATTR_MAX = 4
ATTR_DEFAULT = 5
ATTR_INCREMENT = 6
ATTR_ACCESS = 7
ATTR_AVAIL = 8
ACC_READ_ONLY = 1
ACC_READ_WRITE = 2
ACC_EXIST_CHECK_ONLY = 3
ACC_WRITE_ONLY = 4
IO_TYPE_TTL = 0
IO_TYPE_DAC = 1
IO_DIR_INPUT = 0
IO_DIR_OUTPUT = 1
IO_DIR_INPUT_OUTPUT = 2
READOUT_PORT_0 = 0
READOUT_PORT_1 = 1
CLEAR_NEVER = 0
CLEAR_PRE_EXPOSURE = 1
CLEAR_PRE_SEQUENCE = 2
CLEAR_POST_SEQUENCE = 3
CLEAR_PRE_POST_SEQUENCE = 4
CLEAR_PRE_EXPOSURE_POST_SEQ = 5
MAX_CLEAR_MODE = 6
OPEN_NEVER = 0
OPEN_PRE_EXPOSURE = 1
OPEN_PRE_SEQUENCE = 2
OPEN_PRE_TRIGGER = 3
OPEN_NO_CHANGE = 4
TIMED_MODE = 0
STROBED_MODE = 1
BULB_MODE = 2
TRIGGER_FIRST_MODE = 3
FLASH_MODE = 4
VARIABLE_TIMED_MODE = 5
INT_STROBE_MODE = 6
MAX_EXPOSE_MODE = 7
Extended = 8
camera = 9
The = 10
definition = 11
EXT_TRIG_INTERNAL = 12
EXT_TRIG_TRIG_FIRST = 13
EXT_TRIG_EDGE_RISING = 14
EXPOSE_OUT_FIRST_ROW = 0
EXPOSE_OUT_ALL_ROWS = 1
EXPOSE_OUT_ANY_ROW = 2
MAX_EXPOSE_OUT_MODE = 3
FAN_SPEED_HIGH = 0
FAN_SPEED_MEDIUM = 1
FAN_SPEED_LOW = 2
FAN_SPEED_OFF = 3
PL_TRIGTAB_SIGNAL_EXPOSE_OUT = 0
PP_FEATURE_RING_FUNCTION = 0
PP_FEATURE_BIAS = 1
PP_FEATURE_BERT = 2
PP_FEATURE_QUANT_VIEW = 3
PP_FEATURE_BLACK_LOCK = 4
PP_FEATURE_TOP_LOCK = 5
PP_FEATURE_VARI_BIT = 6
PP_FEATURE_RESERVED = 7
PP_FEATURE_DESPECKLE_BRIGHT_HIGH = 8
PP_FEATURE_DESPECKLE_DARK_LOW = 9
PP_FEATURE_DEFECTIVE_PIXEL_CORRECTION = 10
PP_FEATURE_DYNAMIC_DARK_FRAME_CORRECTION = 11
PP_FEATURE_HIGH_DYNAMIC_RANGE = 12
PP_FEATURE_DESPECKLE_BRIGHT_LOW = 13
PP_FEATURE_DENOISING = 14
PP_FEATURE_DESPECKLE_DARK_HIGH = 15
PP_FEATURE_ENHANCED_DYNAMIC_RANGE = 16
PP_FEATURE_MAX = 17
PP_MAX_PARAMETERS_PER_FEATURE = 10
PP_PARAMETER_RF_FUNCTION = 0
PP_FEATURE_BIAS_ENABLED = 1
PP_FEATURE_BIAS_LEVEL = 2
PP_FEATURE_BERT_ENABLED = 3
PP_FEATURE_BERT_THRESHOLD = 4
PP_FEATURE_QUANT_VIEW_ENABLED = 5
PP_FEATURE_QUANT_VIEW_E = 6
PP_FEATURE_BLACK_LOCK_ENABLED = 7
PP_FEATURE_BLACK_LOCK_BLACK_CLIP = 8
PP_FEATURE_TOP_LOCK_ENABLED = 9
PP_FEATURE_TOP_LOCK_WHITE_CLIP = 10
PP_FEATURE_VARI_BIT_ENABLED = 11
PP_FEATURE_VARI_BIT_BIT_DEPTH = 12
PP_FEATURE_DESPECKLE_BRIGHT_HIGH_ENABLED = 13
PP_FEATURE_DESPECKLE_BRIGHT_HIGH_THRESHOLD = 14
PP_FEATURE_DESPECKLE_BRIGHT_HIGH_MIN_ADU_AFFECTED = 15
PP_FEATURE_DESPECKLE_DARK_LOW_ENABLED = 16
PP_FEATURE_DESPECKLE_DARK_LOW_THRESHOLD = 17
PP_FEATURE_DESPECKLE_DARK_LOW_MAX_ADU_AFFECTED = 18
PP_FEATURE_DEFECTIVE_PIXEL_CORRECTION_ENABLED = 19
PP_FEATURE_DYNAMIC_DARK_FRAME_CORRECTION_ENABLED = 20
PP_FEATURE_HIGH_DYNAMIC_RANGE_ENABLED = 21
PP_FEATURE_DESPECKLE_BRIGHT_LOW_ENABLED = 22
PP_FEATURE_DESPECKLE_BRIGHT_LOW_THRESHOLD = 23
PP_FEATURE_DESPECKLE_BRIGHT_LOW_MAX_ADU_AFFECTED = 24
PP_FEATURE_DENOISING_ENABLED = 25
PP_FEATURE_DENOISING_NO_OF_ITERATIONS = 26
PP_FEATURE_DENOISING_GAIN = 27
PP_FEATURE_DENOISING_OFFSET = 28
PP_FEATURE_DENOISING_LAMBDA = 29
PP_FEATURE_DESPECKLE_DARK_HIGH_ENABLED = 30
PP_FEATURE_DESPECKLE_DARK_HIGH_THRESHOLD = 31
PP_FEATURE_DESPECKLE_DARK_HIGH_MIN_ADU_AFFECTED = 32
PP_FEATURE_ENHANCED_DYNAMIC_RANGE_ENABLED = 33
PP_PARAMETER_ID_MAX = 34
SMTMODE_ARBITRARY_ALL = 0
SMTMODE_MAX = 1
READOUT_NOT_ACTIVE = 0
EXPOSURE_IN_PROGRESS = 1
READOUT_IN_PROGRESS = 2
READOUT_COMPLETE = 3
FRAME_AVAILABLE = 3
READOUT_FAILED = 4
ACQUISITION_IN_PROGRESS = 5
MAX_CAMERA_STATUS = 6
CCS_NO_CHANGE = 0
CCS_HALT = 1
CCS_HALT_CLOSE_SHTR = 2
CCS_CLEAR = 3
CCS_CLEAR_CLOSE_SHTR = 4
CCS_OPEN_SHTR = 5
CCS_CLEAR_OPEN_SHTR = 6
NO_FRAME_IRQS = 0
BEGIN_FRAME_IRQS = 1
END_FRAME_IRQS = 2
BEGIN_END_FRAME_IRQS = 3
CIRC_NONE = 0
CIRC_OVERWRITE = 1
CIRC_NO_OVERWRITE = 2
EXP_RES_ONE_MILLISEC = 0
EXP_RES_ONE_MICROSEC = 1
EXP_RES_ONE_SEC = 2
SCR_PRE_OPEN_SHTR = 0
SCR_POST_OPEN_SHTR = 1
SCR_PRE_FLASH = 2
SCR_POST_FLASH = 3
SCR_PRE_INTEGRATE = 4
SCR_POST_INTEGRATE = 5
SCR_PRE_READOUT = 6
SCR_POST_READOUT = 7
SCR_PRE_CLOSE_SHTR = 8
SCR_POST_CLOSE_SHTR = 9
PL_CALLBACK_BOF = 0
PL_CALLBACK_EOF = 1
PL_CALLBACK_CHECK_CAMS = 2
PL_CALLBACK_CAM_REMOVED = 3
PL_CALLBACK_CAM_RESUMED = 4
PL_CALLBACK_MAX = 5
PL_MD_FRAME_FLAG_ROI_TS_SUPPORTED = 1
PL_MD_FRAME_FLAG_UNUSED_2 = 2
PL_MD_FRAME_FLAG_UNUSED_3 = 4
PL_MD_FRAME_FLAG_UNUSED_4 = 16
PL_MD_FRAME_FLAG_UNUSED_5 = 32
PL_MD_FRAME_FLAG_UNUSED_6 = 64
PL_MD_FRAME_FLAG_UNUSED_7 = 128
PL_MD_ROI_FLAG_INVALID = 1
PL_MD_ROI_FLAG_UNUSED_2 = 2
PL_MD_ROI_FLAG_UNUSED_3 = 4
PL_MD_ROI_FLAG_UNUSED_4 = 16
PL_MD_ROI_FLAG_UNUSED_5 = 32
PL_MD_ROI_FLAG_UNUSED_6 = 64
PL_MD_ROI_FLAG_UNUSED_7 = 128
PL_MD_FRAME_SIGNATURE = 5328208
PL_MD_EXT_TAGS_MAX_SUPPORTED = 255
PL_MD_EXT_TAG_MAX = 0
TYPE_INT16 = 1
TYPE_INT32 = 2
TYPE_FLT64 = 4
TYPE_UNS8 = 5
TYPE_UNS16 = 6
TYPE_UNS32 = 7
TYPE_UNS64 = 8
TYPE_ENUM = 9
TYPE_BOOLEAN = 11
TYPE_INT8 = 12
TYPE_CHAR_PTR = 13
TYPE_VOID_PTR = 14
TYPE_VOID_PTR_PTR = 15
TYPE_INT64 = 16
TYPE_SMART_STREAM_TYPE = 17
TYPE_SMART_STREAM_TYPE_PTR = 18
TYPE_FLT32 = 19
CLASS0 = 0
CLASS2 = 2
CLASS3 = 3
PARAM_DD_INFO_LENGTH = 16777217
PARAM_DD_VERSION = 100663298
PARAM_DD_RETRIES = 100663299
PARAM_DD_TIMEOUT = 100663300
PARAM_DD_INFO = 218103813
PARAM_ADC_OFFSET = 16908483
PARAM_CHIP_NAME = 218235009
PARAM_SYSTEM_NAME = 218235010
PARAM_VENDOR_NAME = 218235011
PARAM_PRODUCT_NAME = 218235012
PARAM_CAMERA_PART_NUMBER = 218235013
PARAM_COOLING_MODE = 151126230
PARAM_PREAMP_DELAY = 100794870
PARAM_COLOR_MODE = 151126520
PARAM_MPP_CAPABLE = 151126240
PARAM_PREAMP_OFF_CONTROL = 117572091
PARAM_PREMASK = 100794421
PARAM_PRESCAN = 100794423
PARAM_POSTMASK = 100794422
PARAM_POSTSCAN = 100794424
PARAM_PIX_PAR_DIST = 100794868
PARAM_PIX_PAR_SIZE = 100794431
PARAM_PIX_SER_DIST = 100794869
PARAM_PIX_SER_SIZE = 100794430
PARAM_SUMMING_WELL = 184680953
PARAM_FWELL_CAPACITY = 117572090
PARAM_PAR_SIZE = 100794425
PARAM_SER_SIZE = 100794426
PARAM_ACCUM_CAPABLE = 184680986
PARAM_FLASH_DWNLD_CAPABLE = 184680987
PARAM_READOUT_TIME = 67240115
PARAM_CLEAR_CYCLES = 100794465
PARAM_CLEAR_MODE = 151126539
PARAM_FRAME_CAPABLE = 184680957
PARAM_PMODE = 151126540
PARAM_TEMP = 16908813
PARAM_TEMP_SETPOINT = 16908814
PARAM_CAM_FW_VERSION = 100794900
PARAM_HEAD_SER_NUM_ALPHA = 218235413
PARAM_PCI_FW_VERSION = 100794902
PARAM_FAN_SPEED_SETPOINT = 151126726
PARAM_EXPOSURE_MODE = 151126551
PARAM_EXPOSE_OUT_MODE = 151126576
PARAM_BIT_DEPTH = 16908799
PARAM_GAIN_INDEX = 16908800
PARAM_SPDTAB_INDEX = 16908801
PARAM_GAIN_NAME = 218235394
PARAM_READOUT_PORT = 151126263
PARAM_PIX_TIME = 100794884
PARAM_SHTR_CLOSE_DELAY = 100794887
PARAM_SHTR_OPEN_DELAY = 100794888
PARAM_SHTR_OPEN_MODE = 151126537
PARAM_SHTR_STATUS = 151126538
PARAM_IO_ADDR = 100794895
PARAM_IO_TYPE = 151126544
PARAM_IO_DIRECTION = 151126545
PARAM_IO_STATE = 67240466
PARAM_IO_BITDEPTH = 100794899
PARAM_GAIN_MULT_FACTOR = 100794905
PARAM_GAIN_MULT_ENABLE = 184680989
PARAM_PP_FEAT_NAME = 218235422
PARAM_PP_INDEX = 16908831
PARAM_ACTUAL_GAIN = 100794912
PARAM_PP_PARAM_INDEX = 16908833
PARAM_PP_PARAM_NAME = 218235426
PARAM_PP_PARAM = 117572131
PARAM_READ_NOISE = 100794916
PARAM_PP_FEAT_ID = 100794917
PARAM_PP_PARAM_ID = 100794918
PARAM_SMART_STREAM_MODE_ENABLED = 184681148
PARAM_SMART_STREAM_MODE = 100795069
PARAM_SMART_STREAM_EXP_PARAMS = 235012798
PARAM_SMART_STREAM_DLY_PARAMS = 235012799
PARAM_EXP_TIME = 100859905
PARAM_EXP_RES = 151191554
PARAM_EXP_RES_INDEX = 100859908
PARAM_EXPOSURE_TIME = 134414344
PARAM_BOF_EOF_ENABLE = 151191557
PARAM_BOF_EOF_COUNT = 117637126
PARAM_BOF_EOF_CLR = 184745991
PARAM_CIRC_BUFFER = 184746283
PARAM_FRAME_BUFFER_SIZE = 134414636
PARAM_BINNING_SER = 151191717
PARAM_BINNING_PAR = 151191718
PARAM_METADATA_ENABLED = 184746152
PARAM_ROI_COUNT = 100860073
PARAM_CENTROIDS_ENABLED = 184746154
PARAM_CENTROIDS_RADIUS = 100860075
PARAM_CENTROIDS_COUNT = 100860076
PARAM_TRIGTAB_SIGNAL = 151191732
PARAM_LAST_MUXED_SIGNAL = 84082869


# === C structures ===
# GUID for #FRAME_INFO structure.
class PVCAM_FRAME_INFO_GUID(ctypes.Structure):
    _fields_ = [("f1", uns32),
                ("f2", uns16),
                ("f3", uns16),
                ("f4", uns8 * 8),]

# Structure used to uniquely identify frames in the camera.
class FRAME_INFO(ctypes.Structure):
    _fields_ = [("FrameInfoGUID", PVCAM_FRAME_INFO_GUID),
                ("hCam", int16),
                ("FrameNr", int32),
                ("TimeStamp", long64),
                ("ReadoutTime", int32),
                ("TimeStampBOF", long64),]


class smart_stream_type(ctypes.Structure):
    _fields_ = [("entries", uns16),
                ("params", uns32),]


class rgn_type(ctypes.Structure):
    _fields_ = [("s1", uns16),
               ("s2", uns16),
               ("sbin", uns16),
               ("p1", uns16),
               ("p2", uns16),
               ("pbin", uns16),]


class io_struct(ctypes.Structure):
    pass

io_struct._fields_ = [("io_port", uns16),
                     ("io_type", uns32),
                     ("state", flt64),
                     ("next", ctypes.POINTER(io_struct))]


class io_list(ctypes.Structure):
    _fields_ = [
        ("pre_open", ctypes.POINTER(io_struct)),
        ("post_open", ctypes.POINTER(io_struct)),
        ("pre_flash", ctypes.POINTER(io_struct)),
        ("post_flash", ctypes.POINTER(io_struct)),
        ("pre_integrate", ctypes.POINTER(io_struct)),
        ("post_integrate", ctypes.POINTER(io_struct)),
        ("pre_readout", ctypes.POINTER(io_struct)),
        ("post_readout", ctypes.POINTER(io_struct)),
        ("pre_close", ctypes.POINTER(io_struct)),
        ("post_close", ctypes.POINTER(io_struct)),
    ]

class active_camera_type(ctypes.Structure):
    _fields_ = [
        ("shutter_close_delay", uns16),
        ("shutter_open_delay", uns16),
        ("rows", uns16),
        ("cols", uns16),
        ("prescan", uns16),
        ("postscan", uns16),
        ("premask", uns16),
        ("postmask", uns16),
        ("preflash", uns16),
        ("clear_count", uns16),
        ("preamp_delay", uns16),
        ("mpp_selectable", rs_bool),
        ("frame_selectable", rs_bool),
        ("do_clear", uns16),
        ("open_shutter", uns16),
        ("mpp_mode", rs_bool),
        ("frame_transfer", rs_bool),
        ("alt_mode", rs_bool),
        ("exp_res", uns32),
        ("io_hdr", ctypes.POINTER(io_list)),
    ]


class md_frame_header(ctypes.Structure):
    _fields_ = [
        ("signature", uns32),
        ("version", uns8 ),
        ("frameNr", uns32),
        ("roiCount", uns16),
        ("timestampBOF", uns32),
        ("timestampEOF", uns32),
        ("timestampResNs", uns32),
        ("exposureTime", uns32),
        ("exposureTimeResN", uns32),
        ("roiTimestampResN", uns32),
        ("bitDepth", uns8),
        ("colorMask", uns8),
        ("flags", uns8),
        ("extendedMdSize", uns16),
        ("_reserved", uns8*8),]


class md_frame_roi_header(ctypes.Structure):
    _fields_ = [
        ("roiNr", uns16),
        ("timestampBOR", uns32),
        ("timestampEOR", uns32),
        ("roi", rgn_type),
        ("flags", uns8),
        ("extendedMdSize", uns16),
        ("_reserved", uns8*7),
    ]


PL_MD_EXT_TAGS_MAX_SUPPORTED = 255

class md_ext_item_info(ctypes.Structure):
    _fields_ = [
        ("tag", uns16),
        ("size", uns16),
        ("name", ctypes.c_char_p),
    ]

class md_ext_item(ctypes.Structure):
    _fields_ = [
        ("tagInfo", ctypes.POINTER(md_ext_item_info)), #
        ("value", ctypes.c_void_p)
    ]


class md_ext_item_collection(ctypes.Structure):
    _fields_ = [
        ("list", md_ext_item*PL_MD_EXT_TAGS_MAX_SUPPORTED),
        ("map", ctypes.POINTER(md_ext_item)*PL_MD_EXT_TAGS_MAX_SUPPORTED),
        ("count", uns16),
    ]

class md_frame_roi(ctypes.Structure):
    _fields_ = [
        ("header", ctypes.POINTER(md_frame_roi_header)),
        ("data", ctypes.c_void_p),
        ("dataSize", uns32),
        ("extMdData", ctypes.c_void_p),
        ("extMdDataSize", uns16),
    ]

class md_frame(ctypes.Structure):
    _fields_ = [
        ("header", ctypes.POINTER(md_frame_header)),
        ("extMdData", ctypes.c_void_p),
        ("extMdDataSize", uns16),
        ("impliedRoi", rgn_type),
        ("roiArray", ctypes.POINTER(md_frame_roi)),
        ("roiCapacity", uns16),
        ("roiCount", uns16),
    ]


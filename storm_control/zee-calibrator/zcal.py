#!/usr/bin/python
#
## @file
#
# Z calibration functions.
#
# Hazen 07/14
#

import math
import numpy
import numpy.lib.recfunctions
import os
import re
import scipy
import scipy.optimize
import struct

#
# different power z calibration functions
#

## zcalib0
#
# Z calibration fitting function with no additional parameters.
#
# @param p Fit parameters.
# @param z Z values.
#
# @return The function at the specified z values.
#
def zcalib0(p, z):
    wo,c,d = p
    X = (z-c)/d
    return wo*numpy.sqrt(1.0 + numpy.power(X,2))

## zcalib1
#
# Z calibration fitting function with 1 additional parameters.
#
# @param p Fit parameters.
# @param z Z values.
#
# @return The function at the specified z values.
#
def zcalib1(p, z):
    wo,c,d,A = p
    X = (z-c)/d
    return wo*numpy.sqrt(1.0 + numpy.power(X,2) + A * numpy.power(X,3))

## zcalib2
#
# Z calibration fitting function with 2 additional parameters.
#
# @param p Fit parameters.
# @param z Z values.
#
# @return The function at the specified z values.
#
def zcalib2(p, z):
    wo,c,d,A,B = p
    X = (z-c)/d
    return wo*numpy.sqrt(1.0 + numpy.power(X,2) + A * numpy.power(X,3) + B * numpy.power(X,4))

## zcalib3
#
# Z calibration fitting function with 3 additional parameters.
#
# @param p Fit parameters.
# @param z Z values.
#
# @return The function at the specified z values.
#
def zcalib3(p, z):
    wo,c,d,A,B,C = p
    X = (z-c)/d
    return wo*numpy.sqrt(1.0 + numpy.power(X,2) + A * numpy.power(X,3) + B * numpy.power(X,4) + C * numpy.power(X,5))

## zcalib4
#
# Z calibration fitting function with 4 additional parameters.
#
# @param p Fit parameters.
# @param z Z values.
#
# @return The function at the specified z values.
#
def zcalib4(p, z):
    wo,c,d,A,B,C,D = p
    X = (z-c)/d
    return wo*numpy.sqrt(1.0 + numpy.power(X,2) + A * numpy.power(X,3) + B * numpy.power(X,4) + C * numpy.power(X,5) + D * numpy.power(X,6))

zcalibs = [zcalib0, zcalib1, zcalib2, zcalib3, zcalib4]


#
# insight3 file reading
#

## getV
#
# Helper function for reading binary header data.
#
# @param fp A file pointer.
# @param format A string defining the data format.
# @param size An integer specifying how many bytes to read.
#
# @return The unpacked value from the file.
#
def getV(fp, format, size):
    return struct.unpack(format, fp.read(size))[0]

## i3DataType
#
# @return A numpy data type to use for reading Insight3 format files.
#
def i3DataType():
    return numpy.dtype([('x', numpy.float32),   # original x location
                        ('y', numpy.float32),   # original y location
                        ('xc', numpy.float32),  # drift corrected x location
                        ('yc', numpy.float32),  # drift corrected y location
                        ('h', numpy.float32),   # fit height
                        ('a', numpy.float32),   # fit area
                        ('w', numpy.float32),   # fit width
                        ('phi', numpy.float32), # fit angle (for unconstrained elliptical gaussian)
                        ('ax', numpy.float32),  # peak aspect ratio
                        ('bg', numpy.float32),  # fit background
                        ('i', numpy.float32),   # sum - baseline for pixels included in the peak
                        ('c', numpy.int32),     # peak category ([0..9] for STORM images)
                        ('fi', numpy.int32),    # fit iterations
                        ('fr', numpy.int32),    # frame
                        ('tl', numpy.int32),    # track length
                        ('lk', numpy.int32),    # link (id of the next molecule in the trace)
                        ('z', numpy.float32),   # original z coordinate
                        ('zc', numpy.float32)]) # drift corrected z coordinate

## maskData
#
# Creates a new i3 data structure containing only
# those elements where mask is True.
#
# @param i3data The insight3 format data.
# @param mask The (numpy) mask.
#
# @return An i3data data structure containing only the localizations where mask was true.
#
def maskData(i3data, mask):
    new_i3data = numpy.zeros(mask.sum(), dtype = i3DataType())
    for field in i3data.dtype.names:
        new_i3data[field] = i3data[field][mask]
    return new_i3data

## posSet
#
# Convenience function for setting both a position
# and it's corresponding drift corrected value.
#
# @param i3data The insight3 format data.
# @param field The field to set.
# @param value The values to set the field to.
#
def posSet(i3data, field, value):
    setI3Field(i3data, field, value)
    setI3Field(i3data, field + 'c', value)

## readHeader
#
# @param fp A file pointer.
#
# @return [# frames, # localizations, file version, file status]
#
def readHeader(fp):
    version = getV(fp, "4s", 4)
    frames = getV(fp, "i", 4)
    status = getV(fp, "i", 4)
    molecules = getV(fp, "i", 4)
    if 0:
        print "Version:", version
        print "Frames:", frames
        print "Status:", status
        print "Molecules:", molecules
        print ""
    return [frames, molecules, version, status]

## readI3File
#
# Read the data from an Insight3 format file.
#
# @param filename The filename of the file including the path.
# @param nm_per_pixel The number of nm per pixel.
#
# @return The localization data.
#
def readI3File(filename, nm_per_pixel):
    print "nm_per_pixel", nm_per_pixel
    fp = open(filename, "rb")

    # Read header
    [frames, molecules, version, status] = readHeader(fp)

    # Read molecule info
    data = numpy.fromfile(fp, dtype = i3DataType())
    data = data[:][0:molecules]
    fp.close()

    return data

#    return [data,
#            data['x'],
#            data['y'],
#            data['c'],
#            data['i'],
#            data['fr'],
#            numpy.sqrt(data['w']*data['w']/data['ax'])/nm_per_pixel,
#            numpy.sqrt(data['w']*data['w']*data['ax'])/nm_per_pixel]


## ZCalibration
#
# A class to encapsulate fitting Z calibration data.
#
class ZCalibration():

    # Initialize
    def __init__(self, filename, fit_power, minimum_intensity, nm_per_pixel):
        self.filename = filename
        self.fit_power = fit_power
        self.nm_per_pixel = nm_per_pixel

        # state variables
        self.edge_loc = 0
        self.frames = None
        self.good_stagep = None
        self.good_offsetp = None
        self.i3_data = None
        self.mask = None
        self.offsets = None
        self.quick_z = None
        self.stage_zero = None
        self.sz = None
        self.tilt = [0.0, 0.0, 0.0]
        self.wx = None
        self.wx_fit = None
        self.wy = None
        self.wy_fit = None
        self.z = None
        self.z_offset = 0

        # Is this a molecule list file?
        if filename is not None:
            if(filename[-4:] == ".bin"):
                self.loadMolecules(filename, minimum_intensity)
            else:
                self.loadCalibration(filename)

    # determine z dependence on wx - wy, this is used to provide
    # a good guess for where to start searching for the right
    # z coordinate using the non-linear "official" method.
    def calcQuickZ(self):
        qz = numpy.arange(-400,400,10)
        diff = zcalibs[self.fit_power](self.wx_fit, qz) - zcalibs[self.fit_power](self.wy_fit, qz)
        self.quick_z = numpy.polyfit(diff, qz, 1)

    # Determines the z location of the point where wx = wy
    # This can then used to constrain the fit to +- 450nm from
    # this point to avoid fitting to far out into the high z tails.
    def findZOffset(self):
        z = numpy.arange(-400,400.5,1.0)
        global zcalibs
        wx = zcalibs[self.fit_power](self.wx_fit, z)
        wy = zcalibs[self.fit_power](self.wy_fit, z)
        i_min_z = numpy.argmin(numpy.abs(wx - wy))
        self.z_offset += z[i_min_z]
        return True

    # Fits the "standard" defocusing curve
    def fitDefocusing(self):
        # collect all the points
        mask = (self.mask != 0)
        [x, y, wx, wy, sz] = self.selectObjects(mask)

        # fit
        global zcalibs
        def f_zcalib(p, w, z):
            return zcalibs[self.fit_power](p, z) - w

        def doFit(aw, params = [2.4, 0.0, 500.0]):
            for i in range(self.fit_power):
                params.append(0.0)
            [results, success] = scipy.optimize.leastsq(f_zcalib, params, args=(aw, sz))
            if (success < 1) or (success > 4):
                return None
            else:
                return results

        self.wx_fit = doFit(wx, params = [3.0, -400.0, 500.0])
        self.wy_fit = doFit(wy, params = [3.0, 400.0, 500.0])
        if (type(self.wx_fit) == type(numpy.array([]))) and (type(self.wy_fit) == type(numpy.array([]))):
            self.calcQuickZ()
            return True
        else:
            # if the fit fails, try again with the initial arguments reversed
            self.wx_fit = doFit(wx, params = [3.0, 400.0, 500.0])
            self.wy_fit = doFit(wy, params = [3.0, -400.0, 500.0])
            if (type(self.wx_fit) == type(numpy.array([]))) and (type(self.wy_fit) == type(numpy.array([]))):
                self.calcQuickZ()
                return True
            else:
                print "fitDefocusing: power", self.fit_power, "fit failed!"
                return False

    # Fits for the stage tilt
    def fitTilt(self):
        
        # get objects in the first (non-moving frames)
        mask = (numpy.arange(self.frames) < self.edge_loc)
        [x, y, wx, wy, sz] = self.selectObjects(mask)

        # determine object z positions, remove those
        # with negative (or high?) error
        [rz, err] = self.objectZCoords(wx, wy)
        mask = (err >= 0.0) # & (err < 0.06)
        rz = rz[mask]
        x = x[mask]
        y = y[mask]

        # find the best fit plane through x,y,z
        def fitfn(p):
            zf = p[0] + p[1]*x + p[2]*y
            return rz - zf
        params = [scipy.mean(rz), 0.0, 0.0]
        [results, success] = scipy.optimize.leastsq(fitfn, params)
        if (success < 1) or (success > 4):
            print "fitTilt: fit failed!"
            return False
        else:
            print results
            self.tilt = results
            return True

    # Get a binned version of the points in the fit
    def getBinnedPoints(self):
        mask = (self.mask != 0)
        [x, y, wx, wy, sz] = self.selectObjects(mask)
        z_cur = -400.0
        z_bin = 20.0
        z_smooth = []
        wx_smooth = []
        wy_smooth = []
        while(z_cur < 410.0):
            mask = (sz >= z_cur) & (sz < z_cur + z_bin)
            z_smooth.append(z_cur + 0.5 * z_bin)
            wx_smooth.append(numpy.average(wx[mask]))
            wy_smooth.append(numpy.average(wy[mask]))
            z_cur += z_bin

        return [numpy.array(z_smooth), 
                numpy.array(wx_smooth),
                numpy.array(wy_smooth)]

    # Return localization category information
    def getCategory(self):
        return self.i3_data['c']

    # Return fit curves
    def getFitValues(self):
        z = numpy.arange(-400,400.5,1.0)
        global zcalibs
        wx = zcalibs[self.fit_power](self.wx_fit, z)
        wy = zcalibs[self.fit_power](self.wy_fit, z)
        return [z, wx, wy]

    # Return the z value of a particular frame
    def getFrameZnm(self, frame):
        return 1000.0 * (self.fit[0] * self.offsets[frame,0] + self.fit[1])

    # Return the points that were used for the fit
    def getPoints(self):
        mask = (self.mask != 0)
        [x, y, wx, wy, sz] = self.selectObjects(mask)
        return [sz, wx, wy]

    # Return stage fit
    def getStageFit(self):
        return self.fit

    # Return stage & qpd values
    def getStageQPD(self):
        return [self.good_stagep, self.good_offsetp]

    # Return the Wx coefficients
    def getWxCoeffs(self):
        coeffs = self.wx_fit.tolist()
        while len(coeffs) < 7:
            coeffs.append(0)
        coeffs[0] = coeffs[0] * self.nm_per_pixel
        return coeffs

    # Return the Wx coefficients as a string
    def getWxString(self):
        coeffs = self.getWxCoeffs()
#        wxstring = "wx0={0:.1f};zrx={2:.1f};gx={1:.1f};Dx={6:.3f};Cx={5:.3f};Bx={4:.3f};Ax={3:.3f};".format(*coeffs)
        wxstring = "wx0=%.1f;zrx=%.1f;gx=%.1f;Dx=%.3f;Cx=%.3f;Bx=%.3f;Ax=%.3f;" % (coeffs[0], coeffs[2], coeffs[1], coeffs[6], coeffs[5], coeffs[4], coeffs[3])
        return wxstring

    # Return the Wy coefficients
    def getWyCoeffs(self):
        coeffs = self.wy_fit.tolist()
        while len(coeffs) < 7:
            coeffs.append(0)
        coeffs[0] = coeffs[0] * self.nm_per_pixel
        return coeffs

    # Return the Wy coefficients as a string
    def getWyString(self):
        coeffs = self.getWyCoeffs()
#        wystring = "wy0={0:.1f};zry={2:.1f};gy={1:.1f};Dy={6:.3f};Cy={5:.3f};By={4:.3f};Ay={3:.3f};".format(*coeffs)
        wystring = "wy0=%.1f;zry=%.1f;gy=%.1f;Dy=%.3f;Cy=%.3f;By=%.3f;Ay=%.3f;" % (coeffs[0], coeffs[2], coeffs[1], coeffs[6], coeffs[5], coeffs[4], coeffs[3])
        return wystring

    ## getWxWyData
    #
    # Return the Wx and Wy of the localizations
    #
    # @return [wx, wy]
    #
    def getWxWyData(self):
        return [self.wx, self.wy]

    # Load calibration information from a calibration (or .ini) file
    def loadCalibration(self, filename):
        wx_re = map(re.compile, [r'wx0=([-\d\.]+);',
                                 r'gx=([-\d\.]+);',
                                 r'zrx=([-\d\.]+);',
                                 r'Ax=([-\d\.]+);',
                                 r'Bx=([-\d\.]+);',
                                 r'Cx=([-\d\.]+);',
                                 r'Dy=([-\d\.]+);'])
        wy_re = map(re.compile, [r'wy0=([-\d\.]+);',
                                 r'gy=([-\d\.]+);',
                                 r'zry=([-\d\.]+);',
                                 r'Ay=([-\d\.]+);',
                                 r'By=([-\d\.]+);',
                                 r'Cy=([-\d\.]+);',
                                 r'Dy=([-\d\.]+);'])
        cal_file = open(filename, "r")
        self.wx_fit = numpy.zeros(7)
        self.wy_fit = numpy.zeros(7)
        while 1:
            line = cal_file.readline()
            if not line: break
            for i, regex in enumerate(wx_re):
                m = regex.search(line)
                if m:
                    self.wx_fit[i] = float(m.group(1))
            for i, regex in enumerate(wy_re):
                m = regex.search(line)
                if m:
                    self.wy_fit[i] = float(m.group(1))

        self.wx_fit[0] = self.wx_fit[0]/self.nm_per_pixel
        self.wy_fit[0] = self.wy_fit[0]/self.nm_per_pixel
        self.fit_power = 4

    ## loadMolecules
    #
    # Load the molecules found by Insight3
    #
    # @param filename The name of the Insight format file to load.
    # @param minimum_intensity The minimum intensity
    #
    def loadMolecules(self, filename, minimum_intensity):
        self.i3_data = readI3File(filename, self.nm_per_pixel)
        self.i3_data = maskData(self.i3_data, (self.i3_data['i'] > minimum_intensity))
        self.i3_data['fr'] -= 1
        self.wx = numpy.sqrt(self.i3_data['w']*self.i3_data['w']/self.i3_data['ax'])/self.nm_per_pixel
        self.wy = numpy.sqrt(self.i3_data['w']*self.i3_data['w']*self.i3_data['ax'])/self.nm_per_pixel

    ## objectZCoords
    #
    # Determines the z coordinates from the x and y widths
    #
    # @param wx The localization widths in x.
    # @param wy The localization widths in y.
    #
    # @return [molecule z location, fit error]
    #
    def objectZCoords(self, wx, wy):

        # roughly estimate z
        qz = self.quick_z[0] * (wx - wy) + self.quick_z[1]

        # figure out appropriate z function
        global zcalibs
        zcalibs_fn = zcalibs[self.fit_power]

        # optimize function
        def D(z, wx_m, wy_m):
            wx_c = zcalibs_fn(self.wx_fit, z)
            wy_c = zcalibs_fn(self.wy_fit, z)
            tx = numpy.sqrt(wx_m) - numpy.sqrt(wx_c)
            ty = numpy.sqrt(wy_m) - numpy.sqrt(wy_c)
            err = numpy.sqrt(tx * tx + ty * ty)
            return err
        
        n_vals = wx.shape[0]
        rz = numpy.zeros((n_vals)) # "real" z, determined only from the moments
        for i in range(n_vals):
            zo = self.quick_z[0] * (wx[i] - wy[i]) + self.quick_z[1]
            rz[i] = scipy.optimize.brent(D, args = (wx[i], wy[i]), brack = [zo - 100.0, zo + 100.0])

        err = numpy.zeros(wx.shape[0])
        return [rz, err]

    ## saveCalibration
    #
    # Save the calibration coefficients in a file.
    #
    # @param filename The file to save the calibration in.
    #
    def saveCalibration(self, filename):
        fp = open(filename, "w")
        string = self.getWxString() + self.getWyString()
        fp.write(string + "\n")
        fp.close()

    ## selectObjects
    #
    # Returns arrays containing the objects in the mask == True 
    # frames that meet the appropriate criteria.
    #
    # @param mask A numpy mask with True in the frames that we want to analyze.
    #
    # @return [x, y, wx, wy, sz] Of the localizations in the correct frames and widths that were not too far from the mean.
    #
    def selectObjects(self, mask):
        i3_x = self.i3_data['x']
        i3_y = self.i3_data['y']
        i3_wx = self.wx
        i3_wy = self.wy

        x = numpy.array(())
        y = numpy.array(())
        sz = numpy.array(()) # i.e. z as determined by the nominal stage position and sample tilt.
        wx = numpy.array(())
        wy = numpy.array(())
        for i in range(self.frames):
            if mask[i]:
                
                f_mask = (self.i3_data['fr'] == i)
                _x = i3_x[f_mask]
                _y = i3_y[f_mask]
                _wx = i3_wx[f_mask]
                _wy = i3_wy[f_mask]

                max_err = 1.5
                mwx = scipy.mean(_wx)
                swx = scipy.std(_wx)
                mwy = scipy.mean(_wy)
                swy = scipy.std(_wy)
                w_mask = (_wx > (mwx - max_err *swx)) & (_wx < (mwx + max_err * swx)) & \
                    (_wy > (mwy - max_err *swy)) & (_wy < (mwy + max_err * swy)) & \
                    ((_wx * _wy) > 2.2)
                    
                x = numpy.concatenate((x, numpy.ascontiguousarray(_x[w_mask])), 0)
                y = numpy.concatenate((y, numpy.ascontiguousarray(_y[w_mask])), 0)
                wx = numpy.concatenate((wx, numpy.ascontiguousarray(_wx[w_mask])), 0)
                wy = numpy.concatenate((wy, numpy.ascontiguousarray(_wy[w_mask])), 0)
                tz = self.getFrameZnm(i) + (self.tilt[0] + self.tilt[1] * _x[w_mask] + self.tilt[2] * _y[w_mask])
                sz = numpy.concatenate((sz, numpy.ascontiguousarray(tz)), 0)

        if self.z_offset != None:
            sz -= self.z_offset
            z_mask = (sz > -400.0) & (sz < 400.0)
            x = x[z_mask]
            y = y[z_mask]
            wx = wx[z_mask]
            wy = wy[z_mask]
            sz = sz[z_mask]

        return x, y, wx, wy, sz

    ## stageCalibration
    #
    # If we have an offset file then we can use the stage positions
    # and the offset data to figure out what the offsets correspond
    # to in nm. As a side effect this also figures out what the "good"
    # range of the data is, i.e. where the stage was moving.
    #
    # @param filename The name of the offset file.
    #
    # @return True/False If everything worked (or not).
    #
    def stageCalibration(self, filename):

        # load offset information
        try:
            if os.path.exists(filename[:-9] + ".off"):
                self.offsets = numpy.loadtxt(filename[:-9] + ".off",
                                             skiprows = 1)
            elif os.path.exists(filename[:-10] + ".off"):
                self.offsets = numpy.loadtxt(filename[:-10] + ".off",
                                             skiprows = 1)
            else:
                self.offsets = numpy.loadtxt(filename, skiprows = 1)
        except:
            return False

        self.offsets = self.offsets[:,1:]
        self.frames = self.offsets.shape[0]
        self.stage_zero = self.offsets[0,2]

        # figure out which are the "good" frames
        self.mask = numpy.zeros((self.frames), dtype = 'int')
        found_edge = 0
        i = 0
        while i < self.frames:
            if found_edge == 1:
                self.mask[i] = 1
            if (i > 0) and (not found_edge):
                if abs(self.offsets[i-1,2] - self.offsets[i,2]) > 0.1:
                    print "Start", i
                    self.edge_loc = i - 2
                    found_edge = 1
                    i += 2
            if (i < self.frames - 4) and found_edge:
                if abs(self.offsets[i+2,2] - self.offsets[i+3,2]) > 0.1:
                    print "End", i
                    i = self.frames
            i += 1

        # select out the offset and stage positions for the "good" frames
        n = int(numpy.sum(self.mask))
        self.good_stagep = numpy.zeros((n))
        self.good_offsetp = numpy.zeros((n))
        i = 0
        for j in range(self.mask.shape[0]):
            if self.mask[j] != 0.0:
                self.good_stagep[i] = self.offsets[j,2] - self.stage_zero
                self.good_offsetp[i] = self.offsets[j,0]
                i += 1
    
        # perform a linear to fit to convert offset to nm
        self.fit = numpy.polyfit(self.good_offsetp, self.good_stagep, 1)
        print "stageCalibration:", self.fit
        
        return True

#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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

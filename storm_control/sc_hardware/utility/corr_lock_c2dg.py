#!/usr/bin/env python
"""
Fit spots for the focus lock using a correlation based approach.

Hazen 04/18
"""
import numpy

import storm_analysis.sa_library.fitting as fitting
import storm_analysis.sa_library.ia_utilities_c as iaUtilsC
import storm_analysis.sa_library.matched_filter_c as matchedFilterC
import storm_analysis.simulator.draw_gaussians_c as dg

import storm_control.sc_hardware.utility.corr_2d_gauss_c as corr2DGauss


class CorrLockFitter(object):

    def __init__(self, roi_size = None, sigma = None, threshold = None, **kwds):
        super().__init__(**kwds)


        self.fg_filter = None
        self.roi_size = roi_size
        self.sigma = sigma

        size = (2*self.roi_size, 2*self.roi_size)
        #self.c2dg = corr2DGauss.Corr2DGaussPyNCG(size = size, sigma = sigma)
        self.c2dg = corr2DGauss.Corr2DGaussCNCG(size = size, sigma = sigma)

        self.mxf = iaUtilsC.MaximaFinder(margin = self.roi_size,
                                         radius = 2 * self.sigma,
                                         threshold = threshold,
                                         z_values = [0.0])

    def cleanup(self):
        self.c2dg.cleanup()
        
    def findFitPeak(self, image):
        """
        Returns the optimal alignment (based on the correlation score) between
        a Gaussian and the brightest peak in the image.
        """
        image = numpy.ascontiguousarray(image, dtype = numpy.float64)

        # Find ROI.
        [mx, my, roi] = self.findROI(image)
        if (mx == 0) and (my == 0):
            return [0, 0, False]

        # Fit for peak location in the ROI.
        return self.fitROI(mx, my, roi)

    def findROI(self, image):
        """
        Finds the ROI.
        """
        assert (image.flags['C_CONTIGUOUS']), "Image is not C contiguous!"
        assert (image.dtype == numpy.float64), "Images is not numpy.float64 type."
        
        self.mxf.resetTaken()

        # Create convolution object, if we have not already done this.
        if self.fg_filter is None:
            fg_psf = fitting.gaussianPSF(image.shape, self.sigma)
            self.fg_filter = matchedFilterC.MatchedFilter(fg_psf)

        # Find peaks.
        smoothed_image = self.fg_filter.convolve(image)
        [x, y, z, h] = self.mxf.findMaxima([smoothed_image], want_height = True)

        # No peaks found check
        if(x.size == 0):
            return [0, 0, False]

        # Slice out ROI.
        max_index = numpy.argmax(h)
        mx = int(round(x[max_index])) + 1
        my = int(round(y[max_index])) + 1
        rs = self.roi_size
        roi = image[my-rs:my+rs,mx-rs:mx+rs]
        roi -= numpy.min(roi)

        return [mx, my, roi]

    def fitROI(self, mx, my, roi):
        """
        Pass to aligner and find optimal offset.
        """
        self.c2dg.setImage(roi)
        [disp, success, fun, status] = self.c2dg.maximize()
        if (success) or (status == 2):
            return [my + disp[0] - 0.5,
                    mx + disp[1] - 0.5,
                    True]
        else:
            return [0, 0, False]



            
                   
            

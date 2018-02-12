#!/usr/bin/env python
"""
Peak finder for use by the camera based focus locks. This 
version requires the storm-analysis project.

Hazen 11/17
"""
import numpy
import tifffile

import storm_analysis.sa_library.dao_fit_c as daoFitC
import storm_analysis.sa_library.fitting as fitting
import storm_analysis.sa_library.ia_utilities_c as iaUtilsC
import storm_analysis.sa_library.matched_filter_c as matchedFilterC

import storm_analysis.simulator.draw_gaussians_c as dg


class LockPeakFinder(object):

    def __init__(self, offset = None, sigma = None, threshold = None, **kwds):
        super().__init__(**kwds)

        self.mfit = None
        self.offset = offset
        self.roi_size = 10
        self.sigma = sigma

        # Filter for smoothing the image for peak finding.
        #
        self.fg_filter = None

        self.mxf = iaUtilsC.MaximaFinder(margin = self.roi_size,
                                         radius = 2 * self.sigma,
                                         threshold = threshold + self.offset,
                                         z_values = [0.0])

    def cleanup(self):
        if self.mfit is not None:
            self.mfit.cleanup(verbose = False)
            #self.fg_filter.cleanup()

    def findFitPeak(self, image):
        """
        Returns the 2D gaussian fit to the brightest peak in the image.
        """
        # Convert image and add offset, this is to keep the MLE fitter from
        # overfitting the background and/or taking logs of zero.
        #
        image = numpy.ascontiguousarray(image, dtype = numpy.float64)
        image += self.offset
        
        self.mxf.resetTaken()

        # Create the peak fitter object, if we have not already done this.
        #
        if self.mfit is None:
            background = numpy.zeros(image.shape)

            # Create convolution filter.
            fg_psf = fitting.gaussianPSF(image.shape, self.sigma)
            self.fg_filter = matchedFilterC.MatchedFilter(fg_psf)

            # Create fitter.
            self.mfit = daoFitC.MultiFitter2DFixed(roi_size = self.roi_size)
            #self.mfit = daoFitC.MultiFitter2D()
            #self.mfit = daoFitC.MultiFitter3D()
            #self.mfit.default_tol = 1.0e-3
            self.mfit.initializeC(image)
            self.mfit.newImage(image)
            self.mfit.newBackground(background)
        else:
            self.mfit.newImage(image)

        # Find peaks.
        smoothed_image = self.fg_filter.convolve(image)
        [x, y, z, h] = self.mxf.findMaxima([smoothed_image], want_height = True)

        # No peaks found check
        if(x.size == 0):
            return [0, 0, False]

        max_index = numpy.argmax(h)

        peaks = {"x" : numpy.array([x[max_index]]),
                 "y" : numpy.array([y[max_index]]),
                 "z" : numpy.array([z[max_index]]),
                 "sigma" : numpy.array([self.sigma])}

        # Pass peaks to fitter & fit.
        self.mfit.newPeaks(peaks, "finder")
        self.mfit.doFit(max_iterations = 50)

        # Check for fit convergence.
        if (self.mfit.getUnconverged() == 0):
            # Return peak location.
            x = self.mfit.getPeakProperty("x")
            y = self.mfit.getPeakProperty("y")
            return [y[0], x[0], True]
        else:
            return [0, 0, False]


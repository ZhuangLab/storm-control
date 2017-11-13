#!/usr/bin/env python
"""
Peak finder for use by the camera based focus locks.

Hazen 11/17
"""
import numpy
import tifffile

import storm_analysis.sa_library.dao_fit_c as daoFitC
import storm_analysis.sa_library.ia_utilities_c as iaUtilsC
import storm_analysis.simulator.draw_gaussians_c as dg


class LockPeakFinder(object):

    def __init__(self, sigma = None, threshold = None, **kwds):
        super().__init__(**kwds)

        self.mfit = None
        self.sigma = sigma

        # The 10 pixel margin is a hard coded property of the 3D-DAOSTORM
        # fitter in storm-analysis (storm_analysis/sa_library/dao_fit.c).
        #
        self.mxf = iaUtilsC.MaximaFinder(margin = 10,
                                         radius = 2 * self.sigma,
                                         threshold = threshold,
                                         z_values = [0.0])

    def cleanup(self):
        if self.mfit is not None:
            self.mfit.cleanup()

    def findFitPeak(self, image):
        """
        Returns the 2D gaussian fit to the brightest peak in the image.
        """
        image = numpy.ascontiguousarray(image, dtype = numpy.float64)
        self.mxf.resetTaken()

        # Create the peak fitter object, if we have not already done this.
        #
        if self.mfit is None:
            background = numpy.zeros(image.shape)
            self.mfit = daoFitC.MultiFitter2D()
            self.mfit.initializeC(image)
            self.mfit.newImage(image)
            self.mfit.newBackground(background)
        else:
            self.mfit.newImage(image)

        # Find peaks.
        [x, y, z, h] = self.mxf.findMaxima([image], want_height = True)

        # No peaks found check
        if(x.size == 0):
            return [0, 0, False]
#        else:
#            print(numpy.max(image))
#            print(x,y,h)
#            print()

        max_index = numpy.argmax(h)

        peaks = {"x" : numpy.array([x[max_index]]),
                 "y" : numpy.array([y[max_index]]),
                 "z" : numpy.array([z[max_index]]),
                 "sigma" : numpy.array([self.sigma])}

        # Pass peaks to fitter & fit.
        self.mfit.newPeaks(peaks, "finder")
        self.mfit.doFit()

        # Return peak location.
        x = self.mfit.getPeakProperty("x")
        y = self.mfit.getPeakProperty("y")

        return [y[0], x[0], True]


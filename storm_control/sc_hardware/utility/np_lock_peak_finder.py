#!/usr/bin/env python
"""
Peak finder for use by the camera based focus locks. This 
version uses numpy/scipy only.

Hazen 11/17
"""
import numpy
import scipy
import scipy.optimize
import time

import storm_control.sc_library.hdebug as hdebug

last_warning_time = None

def fitAFunctionLS(data, params, fn):
    """
    Does least squares fitting of a function.
    """
    start_time = time.time()
    result = params
    errorfunction = lambda p: numpy.ravel(fn(*p)(*numpy.indices(data.shape)) - data)
    good = True
    [result, cov_x, infodict, mesg, success] = scipy.optimize.leastsq(errorfunction, params, full_output = 1, maxfev = 500)
    if (success < 1) or (success > 4):
        hdebug.logText("Fitting problem: " + mesg)
        #print "Fitting problem:", mesg
        good = False
    end_time = time.time()

    if (infodict["nfev"] > 70) or ((end_time - start_time) > 0.1):
        
        global last_warning_time
        if last_warning_time is None or ((time.time() - last_warning_time) > 2.0):
            print("> QPD-480 Slow fitting detected")
            print(">", infodict["nfev"], time.time() - start_time)
            print(">", params)
            print(">", result)
            print()
            last_warning_time = time.time()
        
    return [result, good]

def symmetricGaussian(background, height, center_x, center_y, width):
    """
    Returns a function that will return the amplitude of a symmetric 2D-gaussian at a given x, y point.
    """
    return lambda x,y: background + height*numpy.exp(-(((center_x-x)/width)**2 + ((center_y-y)/width)**2) * 2)

def fixedEllipticalGaussian(background, height, center_x, center_y, width_x, width_y):
    """
    Returns a function that will return the amplitude of a elliptical gaussian (constrained to be oriented
    along the XY axis) at a given x, y point.
    """
    return lambda x,y: background + height*numpy.exp(-(((center_x-x)/width_x)**2 + ((center_y-y)/width_y)**2) * 2)

def fitSymmetricGaussian(data, sigma):
    """
    Fits a symmetric gaussian to the data.
    """
    params = [numpy.min(data),
              numpy.max(data),
              0.5 * data.shape[0],
              0.5 * data.shape[1],
              2.0 * sigma]
    return fitAFunctionLS(data, params, symmetricGaussian)

def fitFixedEllipticalGaussian(data, sigma):
    """
    Fits a fixed-axis elliptical gaussian to the data.
    """
    params = [numpy.min(data),
              numpy.max(data),
              0.5 * data.shape[0],
              0.5 * data.shape[1],
              2.0 * sigma,
              2.0 * sigma]
    return fitAFunctionLS(data, params, fixedEllipticalGaussian)


#1D gaussian functions for fit1DGaussian_curvefit
def gaussian1D(x, background, height, center_x, width):
    return background + height*numpy.exp((-(x-center_x)**2)/(2*width**2))

def gaussian1DnoBkg(x, height, center_x, width):
    return height*numpy.exp((-(x-center_x)**2)/(2*width**2))

# this uses the routine curve_fit and has some problems right now
def fit1DGaussian(data, sigma):
    #Sums the data vertically
    #Fits data to a 1D gaussian profile
    #then uses that fit to only fit the peak region (for hopefully better shape)
    start_time = time.time()
    good = True
    profile = numpy.sum(data,0)
    x_ind = numpy.arange(len(profile))
    result = [numpy.min(profile), numpy.max(profile), numpy.argmax(profile), sigma]
    #fit full profile
    try:
        params, cov = scipy.optimize.curve_fit(
                        gaussian1D 
                        ,x_ind, profile
                        ,[numpy.min(profile), numpy.max(profile), numpy.argmax(profile), sigma]
                        #,bounds = ((0,2*numpy.max(profile)),(0, len(profile)-1),(0,len(profile)/2.))
                        )
    except:
        good = False
        print('failed to fit 1D gaussian profile pass 1, RuntimeError')
        hdebug.logText("Fitting problem with 1D Gaussian")

    #fit two a second gaussian but only within 2 sigma of the peak
    if good == True and len(params) == 4:
        params = numpy.absolute(params)
        params2 = params[1:]
        if params[2] > 2*params[3]+1 and params[2] < (len(profile) - 2*params[3] + 1):
        #print(params)
            try:
                params2, cov = scipy.optimize.curve_fit(
                        gaussian1DnoBkg, 
                        x_ind[int(params[2]- 2*params[3]):int(params[2]+2*params[3])],
                        profile[int(params[2]-2*params[3]):int(params[2]+2*params[3])], 
                        params[1:])
            except:
                print('failed to fit 1D gaussian profile pass 2, RuntimeError')
                hdebug.logText("Fitting problem with 1D Gaussian")
                good = False
    if good == True:
        result = params2
        #print(params2)
    else:
        #result output is [amplitude, center, width]
        result = [0,len(profile)/2,sigma]
    end_time = time.time()
    if((end_time - start_time) > 0.1):
        global last_warning_time
        if last_warning_time is None or ((time.time() - last_warning_time) > 2.0):
            print("> QPD-480 Slow fitting detected")
            print(">", time.time() - start_time)
            #print(">", params)
            print(">", result)
            print()
            last_warning_time = time.time()
    return [result, good]

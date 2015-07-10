#!/usr/bin/env python
#
## @file
#
# Generate a pattern for the SLM.
#
# Hazen 01/15
#

import numpy
import scipy
import scipy.misc
import sys

size_x = 1080
size_y = 1920
image = numpy.zeros((size_x, size_y)) + 127.0

# vertical grating.
if 0:
    for i in range(size_y):
        image[:,i] += -51.2 * i

# horizontal grating.
if 1:
    for i in range(size_x):
        image[i,:] += -51.2 * i

# Additional pattern.

midx = size_x/2
midy = size_y/2

# focus.
if 0:
    for i in range(size_x):
        for j in range(size_y):
            dx = (i - midx)
            dy = (j - midy)
            mag = -3.0e-2 * (dx * dx + dy * dy)
            image[i,j] += mag

# horizontal astigmatism
if 1:
    for i in range(size_y):
        dy = (i - midy) + 50
        mag = 0.07 * dy * dy
        image[:,i] += mag
    for i in range(size_x):
        dx = (i - midx) - 50
        if (abs(dx) > 200):
            image[i,:] = 127.0

# vertical astigmatism
if 0:
    for i in range(size_x):
        dx = (i - midx) + xoffset
        mag = 0.2 * dx * dx
        image[i,:] += mag
        #if (abs(dx) > 25):
        #    image[i,:] = 127
    for i in range(size_y):
        dx = (i - midy) + yoffset    
        if (abs(dx) > 100):
            image[:,i] = 127.0

# light grid
if 0:
    cx = midx + 150
    cy = midy
    temp = numpy.copy(image)
    image = numpy.zeros((size_x, size_y)) + 127.0
    image[(cx-150):(cx+150),(cy+150):(cy+200)] = temp[(cx-150):(cx+150),(cy+150):(cy+200)]
    image[(cx-150):(cx+150),(cy-200):(cy-150)] = temp[(cx-150):(cx+150),(cy-200):(cy-150)]
    image[(cx+150):(cx+200),(cy-100):(cy+100)] = temp[(cx+150):(cx+200),(cy-100):(cy+100)]
    image[(cx-200):(cx-150),(cy-100):(cy+100)] = temp[(cx-200):(cx-150),(cy-100):(cy+100)]

# hole
if 0:
    cx = midx + xoffset
    cy = midy + yoffset
    for i in range(size_x):
        for j in range(size_y):
            dx = (i - cx)
            dy = (j - cy)
            if ((dx*dx + dy*dy) < (150*150)):
                image[i,j] = 127.0

# reduce na
if 0:
    cx = midx + xoffset
    cy = midy + yoffset
    for i in range(size_x):
        for j in range(size_y):
            dx = (i - cx)
            dy = (j - cy)
            if ((dx*dx + dy*dy) > (100*100)):
                image[i,j] = 127.0

# ring
if 0:
    cx = midx + 150
    cy = midy
    for i in range(size_x):
        for j in range(size_y):
            dx = (i - cx)
            dy = (j - cy)
            if ((dx*dx + dy*dy) > (300*300)):
                image[i,j] = 127.0
            elif ((dx*dx + dy*dy) < (250*250)):
                image[i,j] = 127.0

# airy beam
if 0:
    cx = midx + 50
    cy = midy - 50
    for i in range(size_x):
        for j in range(size_y):
            dx = (i - cx)
            dy = (j - cy)
            mag = 1.0e-4 * (dx * dx * dx + dy * dy * dy)
            image[i,j] += mag

image = numpy.round(image).astype(numpy.uint8)

scipy.misc.imsave(sys.argv[1], image)


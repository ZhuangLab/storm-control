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

image = numpy.zeros((1080,1920)) + 127.0

# Grating.
for i in range(1920):
    image[:,i] += -51.2 * i

# Additional pattern.

midx = 1920/2
midy = 1080/2

# focus.
if 1:
    for i in range(1920):
        for j in range(1080):
            dx = (i - midx)
            dy = (j - midy)
            mag = -3.0e-2 * (dx * dx + dy * dy)
            image[j,i] += mag

# horizontal astigmatism
if 0:
    for i in range(1920):
        dx = (i - midx)
        mag = 1.0e-1 * dx * dx
        image[:,i] += mag

# vertical astigmatism
if 1:
    for i in range(1080):
        dy = (i - midy)
        mag = 1.0e-1 * dy * dy
        image[i,:] += mag

image = numpy.round(image).astype(numpy.uint8)

scipy.misc.imsave(sys.argv[1], image)


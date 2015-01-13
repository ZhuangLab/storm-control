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

image = numpy.zeros((1080,1920)) + 127.0

# 1st order grating.
#vals = [229, 178, 127, 76, 25]
#for i in range(1920):
#    image[:,i] = vals[(i%len(vals))]

for i in range(1920):
    image[:,i] += -51.2 * i

# Additional pattern.
#midx = 1920/2
#midy = 1080/2
#for i in range(1920):
#    for j in range(1080):
#        dx = (i - midx)
#        dy = (j - midy)
#        mag = round(1.0e-4 * (dx * dx + dy * dy))
#        image[j,i] += mag

image = numpy.round(image).astype(numpy.uint8)

scipy.misc.imsave("grating.png", image)


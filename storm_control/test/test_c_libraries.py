#!/usr/bin/env python
"""
Tests of the C libraries.
"""
import numpy


def testCImageManipulation():
    import storm_control.hal4000.halLib.c_image_manipulation_c as cIM

    # Create a random image.
    nim = numpy.random.randint(200, size = (64,64)).astype(numpy.uint16)
    
    all_ori = [[False, False, False],
               [False, False, True],
               [False, True, False],
               [False, True, True],
               [True, False, False],
               [True, False, True],
               [True, True, False],
               [True, True, True]]
    
    for ori in all_ori:
        [flip_h, flip_v, transpose] = ori
        
        for max_v in [None, 101]:
            [c_nim, c_image_min, c_image_max] = cIM.rescaleImage(nim, flip_h, flip_v, transpose, [0, 100], max_v)
            [py_nim, py_image_min, py_image_max] = cIM.rescaleImage(nim, flip_h, flip_v, transpose, [0, 100], max_v, True)

            # Convert to integer so that we don't have overflow issues when we
            # compare for differences between the two images.
            c_nim = c_nim.astype(numpy.int)
            py_nim = py_nim.astype(numpy.int)

            assert(c_image_min == py_image_min)
            assert(c_image_max == py_image_max)
            assert(numpy.allclose(c_nim, py_nim, atol = 1.1))



def testFocusQuality():
    import storm_control.hal4000.camera.frame as frame
    import storm_control.hal4000.focusLock.focusQuality as fq
    
    image_x = 256
    image_y = 256

    # Gradient in 'x' direction is measured.
    image = numpy.ones((image_x, image_y), dtype = numpy.uint16)
    image[:, 100] = 2
    
    a_frame = frame.Frame(image, 0, image_x, image_y, "na")

    grad = fq.imageGradient(a_frame)
    assert(grad == 2.0 * image_x / (image_x * image_y))

    # Gradient in 'y' direction is not measured.
    image = numpy.ones((image_x, image_y), dtype = numpy.uint16)
    image[100, :] = 2
    
    a_frame = frame.Frame(image, 0, image_x, image_y, "na")

    grad = fq.imageGradient(a_frame)
    assert(grad == 0.0)
    

def testLMMoment():
    import storm_control.hal4000.camera.frame as frame
    import storm_control.hal4000.spotCounter.lmmObjectFinder as lof
    
    lof.initialize()

    image_x = 1024
    image_y = 1024

    image = numpy.ones((image_x, image_y), dtype = numpy.uint16)
    image[200, 100] = 200
    
    a_frame = frame.Frame(image, 0, image_x, image_y, "na")
    
    [x, y, n] = lof.findObjects(a_frame, 100)
    assert(x[0] == 100.0)
    assert(y[0] == 200.0)
    assert(n == 1)

    lof.cleanUp()


if (__name__ == "__main__"):
    testCImageManipulation()
    testFocusQuality()
    testLMMoment()
    
    

#!/usr/bin/python
#
# Interface to logitech dual action joystick.
#
# Hazen 9/12
#

import pygame

ref_count = 0

class DualAction():
    def __init__(self, id = 0, verbose = False):
        global ref_count
        ref_count += 1
        pygame.joystick.init()
        self.jstick = pygame.joystick.Joystick(id)
        self.jstick.init()
        if verbose:
            print "Name:", self.jstick.get_name()
            print "Axes:", self.jstick.get_numaxes()
            print "Trackballs:", self.jstick.get_numballs()
            print "Buttons:", self.jstick.get_numbuttons()
            print "Hats:", self.jstick.get_numhats()

    def getAxis(self, axis):
        return self.jstick.get_axis(axis)

    def getButton(self, button):
        return self.jstick.get_button(button)

    def getHat(self, hat):
        return self.jstick.get_hat(hat)

    def getNumberAxis(self):
        return self.jstick.get_numaxes()

    def getNumberButtons(self):
        return self.jstick.get_numbuttons()

    def getNumberHats(self):
        return self.jstick.get_numhats()

    def shutDown(self):
        self.jstick.quit()
        global ref_count
        ref_count -= 1
        if(ref_count == 0):
            pygame.joystick.quit()


#
# Testing
#

if __name__ == "__main__":
    js = DualAction(verbose = True)
    print "Axis test:"
    for i in range(4):
        print " - ", i, js.getAxis(i)
    print "Button test:"
    for i in range(12):
        print " - ", i, js.getButton(i)
    print "Hat test:"
    for i in range(1):
        print " - ", i, js.getHat(i)
    js.shutDown()


#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
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


#!/usr/bin/python
#
# Handles the plotting window
#
# Hazen 11/11
#

from PyQt4 import QtCore, QtGui

import numpy

import plplot
import plplot_pyqt4

class PlotWindow(QtGui.QWidget):
    def __init__(self, parent = None):
        super(PlotWindow, self).__init__(parent)

        # create plotting widget
        self.plot = plplot_pyqt4.QtExtWidget(842,
                                             595,
                                             self)
        plot_layout = QtGui.QHBoxLayout()
        plot_layout.addWidget(self.plot)
        self.setLayout(plot_layout)
        plplot_pyqt4.plsetqtdev(self.plot)

        # initialize
        plplot.plsdev("extqt")
        plplot.plscol0(0, 255, 255, 255)
        plplot.plscol0(1, 0, 0, 0)
        plplot.plscol0(2, 255, 0, 0)
        plplot.plscol0(3, 0, 255, 0)
        plplot.plscol0(4, 0, 0, 255)
        plplot.plinit()

    def clear(self):
        self.plot.clearWidget()

    def paintEvent(self, event):
        self.plot.show()

    def plotBinnedData(self, b_sz, b_wx, b_wy):
        plplot.plcol0(1)
        plplot.plpoin(b_sz, b_wx, 9)
        plplot.plpoin(b_sz, b_wy, 9)

    def plotData(self, sz, wx, wy):
        self.clear()
        self.plotInit("z_graph")
        plplot.plcol0(2)
        plplot.plpoin(sz, wx, 1)
        plplot.plcol0(3)
        plplot.plpoin(sz, wy, 1)

    def plotFit(self, sz, xfit, yfit):
        plplot.plcol0(4)
        plplot.plline(sz, xfit)
        plplot.plline(sz, yfit)

    def plotInit(self, type):
        plplot.pladv(0)
        plplot.plcol0(1)
        if (type == "z_graph"):
            plplot.plvasp(0.707)
            plplot.plwind(-500, 500, 0, 6.0)
            plplot.plcol0(1)
            plplot.plbox("bcnst", 0, 0, "bcnst", 0, 0)
            plplot.pllab("Z (nm)", "Wx, Wy (pixels)", "Z Versus Wx, Wy")
        if (type == "wx_vs_wy"):
            plplot.plvasp(1.0)
            plplot.plwind(1.0, 5.0, 1.0, 5.0)
            plplot.plcol0(1)
            plplot.plbox("bcnst", 0, 0, "bcnst", 0, 0)
            plplot.pllab("Wx (pixels)", "Wy (pixels)", "Wx Versus Wy")
        if (type == "stage"):
            plplot.plvasp(0.707)
            plplot.plwind(-1.0, 1.0, -0.5, 0.5)
            plplot.plcol0(1)
            plplot.plbox("bcnst", 0, 0, "bcnst", 0, 0)
            plplot.pllab("Stage Position (um)", "QPD offset (au)", "Stage Calibration")

    def plotStageQPD(self, stage, qpd, slope, offset):
        plplot.plcol0(1)
        plplot.plpoin(stage, qpd, 1)
        x0 = numpy.min(qpd)
        x1 = numpy.max(qpd)
        y0 = x0*slope + offset
        y1 = x1*slope + offset
        print x0, x1, y0, y1, offset, slope
        plplot.plcol0(2)
        plplot.plline([y0,y1],[x0,x1])

    def plotWxWyData(self, wx, wy, cat):
        max_points = 20000.0
        points = int(wx.shape[0])
        if (points > max_points):
            mask = numpy.random.random(points)
            reject = max_points/float(points)
            mask = (mask < (max_points/float(points)))
            pwx = wx[mask]
            pwy = wy[mask]
            pc = cat[mask]
        else:
            pwx = wx
            pwy = wy
            pc = cat

        if 0:
            bad_mask = (pc == 9)
            plplot.plcol0(2)
            plplot.plpoin(pwx[bad_mask], pwy[bad_mask], 1)

            good_mask = (pc != 9)
            plplot.plcol0(3)
            plplot.plpoin(pwx[good_mask], pwy[good_mask], 1)
        else:
            plplot.plcol0(2)
            plplot.plpoin(pwx, pwy, 1)

#        print "Fraction bad:", float(bad_mask

    def plotWxWyFit(self, wxfit, wyfit):
        plplot.plcol0(4)
        plplot.plline(wxfit, wyfit)

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



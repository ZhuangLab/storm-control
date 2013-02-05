#!/usr/bin/python
#
# Handles the plotting window
#
# Hazen 02/13
#

from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt

import numpy

class PlotWindow(QtGui.QWidget):

    def __init__(self, x_label, x_range, y_label, y_range, parent):
        QtGui.QWidget.__init__(self, parent)
        self.curves = []

        self.plot = Qwt.QwtPlot(self)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.plot)
        self.setLayout(layout)

        self.plot.setCanvasBackground(QtCore.Qt.white)
        self.plot.setAxisTitle(Qwt.QwtPlot.xBottom, x_label)
        self.plot.setAxisScale(Qwt.QwtPlot.xBottom, x_range[0], x_range[1], x_range[2])
        self.plot.setAxisTitle(Qwt.QwtPlot.yLeft, y_label)
        self.plot.setAxisScale(Qwt.QwtPlot.yLeft, y_range[0], y_range[1], y_range[2])

#        if square:
#            self.rescaler = Qwt.QwtPlotRescaler(self.plot.canvas())
#            self.rescaler.setReferenceAxis(Qwt.QwtPlot.xBottom)
#            self.rescaler.setAspectRatio(Qwt.QwtPlot.yLeft, 1.0)
#            self.rescaler.setAspectRatio(Qwt.QwtPlot.yRight, 0.0)
#            self.rescaler.setAspectRatio(Qwt.QwtPlot.xTop, 0.0)

    def clear(self):
        pass

    def plotBinnedData(self, b_sz, b_wx, b_wy):
        pass

    def plotData(self, sz, wx, wy):
        pass

    def plotFit(self, sz, xfit, yfit):
        pass

    def plotStageQPD(self, stage, qpd, slope, offset):
        pass

    def plotWxWyData(self, wx, wy, cat):
        pass

    def plotWxWyFit(self, wxfit, wyfit):
        pass

class SquarePlotWindow(PlotWindow):

    def __init__(self, x_label, x_range, y_label, y_range, parent):
        PlotWindow.__init__(self, x_label, x_range, y_label, y_range, parent)

        policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        #policy = QtGui.QSizePolicy()
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

    def heightForWidth(self, w):
        print "hFW:", w
        return w

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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



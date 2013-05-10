#!/usr/bin/python
#
# Handles the plotting window
#
# Hazen 02/13
#

from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt

import numpy

def createCurve(pen, brush, symbol_size):
    curve = Qwt.QwtPlotCurve('')
    curve.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
    curve.setPen(pen)
    if (symbol_size > 0):
        curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
                                      brush,
                                      pen,
                                      QtCore.QSize(symbol_size, symbol_size)))
        curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
    return curve

class ZeePlot(Qwt.QwtPlot):

    def __init__(self, parent):
        Qwt.QwtPlot.__init__(self, parent)
        self.static_text = False

    def drawCanvas (self, p):
        Qwt.QwtPlot.drawCanvas(self, p)

        if self.static_text:
            p.drawStaticText(10, 10, self.static_text)

    def setStaticText(self, text):
        self.static_text = text

class PlotWindow(QtGui.QWidget):

    def __init__(self, x_label, x_range, y_label, y_range, parent):
        QtGui.QWidget.__init__(self, parent)
        self.curves = []
        self.text = False

        self.plot = ZeePlot(self)
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
        for curve in self.curves:
            curve.detach()

    def plotBinnedData(self, b_sz, b_wx, b_wy):
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidth(2)
        curve = createCurve(pen,
                            QtGui.QBrush(),
                            9)
        curve.setData(b_sz, b_wx)
        curve.attach(self.plot)
        self.curves.append(curve)

        curve = createCurve(pen,
                            QtGui.QBrush(),
                            9)
        curve.setData(b_sz, b_wy)
        curve.attach(self.plot)
        self.curves.append(curve)
        self.plot.replot()

    def plotData(self, sz, wx, wy):
        curve = createCurve(QtGui.QPen(QtCore.Qt.red),
                            QtGui.QBrush(QtCore.Qt.red),
                            3)
        curve.setData(sz, wx)
        curve.attach(self.plot)
        self.curves.append(curve)

        curve = createCurve(QtGui.QPen(QtCore.Qt.green),
                            QtGui.QBrush(QtCore.Qt.green),
                            3)
        curve.setData(sz, wy)
        curve.attach(self.plot)
        self.curves.append(curve)
        self.plot.replot()

    def plotFit(self, sz, xfit, yfit):
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidth(2)
        curve = createCurve(pen,
                            QtGui.QBrush(),
                            0)
        curve.setData(sz, xfit)
        curve.attach(self.plot)
        self.curves.append(curve)

        curve = createCurve(pen,
                            QtGui.QBrush(),
                            0)
        curve.setData(sz, yfit)
        curve.attach(self.plot)
        self.curves.append(curve)
        self.plot.replot()

    def plotStageQPD(self, stage, qpd, slope, offset):

        qpd_min = numpy.min(qpd)
        qpd_max = numpy.max(qpd)

        self.plot.setAxisScale(Qwt.QwtPlot.yLeft, 1.1*qpd_min, 1.1*qpd_max)

        curve = createCurve(QtGui.QPen(QtCore.Qt.black),
                            QtGui.QBrush(),
                            7)
        curve.setData(stage, qpd)
        curve.attach(self.plot)
        self.curves.append(curve)
        self.plot.replot()

        x_vals = numpy.array([-1.0, 1.0])
        y_vals = (x_vals - offset)/slope

        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidth(2)
        curve = createCurve(pen,
                            QtGui.QBrush(),
                            0)
        curve.setData(x_vals, y_vals)
        curve.attach(self.plot)
        self.curves.append(curve)

        self.plot.setStaticText(QtGui.QStaticText("slope = {0:.3f} au/um".format(-1.0/slope)))

        self.plot.replot()

    def plotWxWyData(self, wx, wy, cat):
        curve = createCurve(QtGui.QPen(QtCore.Qt.red),
                            QtGui.QBrush(QtCore.Qt.red),
                            3)
        curve.setData(wx, wy)
        curve.attach(self.plot)
        self.curves.append(curve)
        self.plot.replot()

    def plotWxWyFit(self, wxfit, wyfit):
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidth(2)
        curve = createCurve(pen,
                            QtGui.QBrush(),
                            0)
        curve.setData(wxfit, wyfit)
        curve.attach(self.plot)
        self.curves.append(curve)
        self.plot.replot()

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



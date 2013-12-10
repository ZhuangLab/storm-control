#!/usr/bin/python
#
# Handles the plotting window
#
# Hazen 02/13
#

from PyQt4 import QtCore, QtGui
import pyqtgraph
#import PyQt4.Qwt5 as Qwt

import numpy

pyqtgraph.setConfigOption('background', 'w')
pyqtgraph.setConfigOption('foreground', 'k')

def createCurve(pen, brush, symbol_size):
    pass
#    curve = Qwt.QwtPlotCurve('')
#    curve.setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
#    curve.setPen(pen)
#    if (symbol_size > 0):
#        curve.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Ellipse,
#                                      brush,
#                                      pen,
#                                      QtCore.QSize(symbol_size, symbol_size)))
#        curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
#    return curve

#class ZeePlot(pyqtgraph.ViewBox):
#
#    def __init__(self, parent, x_range, y_range):
#        pyqtgraph.ViewBox.__init__(self, parent)
#        self.static_text = False
#
#    def drawCanvas (self, p):
#        Qwt.QwtPlot.drawCanvas(self, p)
#
#        if self.static_text:
#            p.drawStaticText(10, 10, self.static_text)
#
#    def setStaticText(self, text):
#        self.static_text = text

class PlotWindow(pyqtgraph.PlotWidget):

    def __init__(self, x_label, x_range, y_label, y_range, qt_parent):
        pyqtgraph.PlotWidget.__init__(self)

        self.viewbox = self.getPlotItem().getViewBox()
        self.viewbox.disableAutoRange()
        self.viewbox.setMouseEnabled(x = False, y = False)
        self.viewbox.setRange(xRange = (x_range[0], x_range[1]),
                              yRange = (y_range[0], y_range[1]))

        self.setLabel('left', y_label)
        self.setLabel('bottom', x_label)

#    def clear(self):
#        pass
#        for curve in self.curves:
#            curve.detach()

    def plotBinnedData(self, b_sz, b_wx, b_wy):
        a_pen = QtGui.QPen(QtCore.Qt.black)
        a_pen.setWidth(2)
        a_brush = QtGui.QBrush(QtGui.QColor(255,255,255,0))
        self.plot(b_sz, b_wx, 
                  pen = None,
                  symbol = 'o',
                  symbolPen = a_pen,
                  symbolBrush = a_brush,
                  symbolSize = 9)

        self.plot(b_sz, b_wy,
                  pen = None,
                  symbol = 'o',
                  symbolPen = a_pen,
                  symbolBrush = a_brush,
                  symbolSize = 9)

    def plotData(self, sz, wx, wy):
        self.plot(sz, wx, 
                  pen = None,
                  symbol = 'o',
                  symbolPen = QtGui.QPen(QtCore.Qt.red),
                  symbolBrush = QtGui.QBrush(QtCore.Qt.blue),
                  symbolSize = 3)

        self.plot(sz, wy, 
                  pen = None,
                  symbol = 'o',
                  symbolPen = QtGui.QPen(QtCore.Qt.green),
                  symbolBrush = QtGui.QBrush(QtCore.Qt.blue),
                  symbolSize = 3)

    def plotFit(self, sz, xfit, yfit):
        a_pen = QtGui.QPen(QtCore.Qt.black)
        self.plot(sz, xfit, pen = a_pen)
        self.plot(sz, yfit, pen = a_pen)

    def plotStageQPD(self, stage, qpd, slope, offset):
        qpd_min = numpy.min(qpd)
        qpd_max = numpy.max(qpd)
        self.viewbox.setRange(yRange = (1.1*qpd_min, 1.1*qpd_max))
        self.plot(stage, qpd,
                  pen = None,
                  symbol = 'o',
                  symbolPen = QtGui.QPen(QtCore.Qt.black),
                  symbolBrush = QtGui.QBrush(QtCore.Qt.white),
                  symbolSize = 7)

        x_vals = numpy.array([-1.0, 1.0])
        y_vals = (x_vals - offset)/slope
        self.plot(x_vals, y_vals, pen = QtGui.QPen(QtCore.Qt.black))

#
#        self.plot.setAxisScale(Qwt.QwtPlot.yLeft, 1.1*qpd_min, 1.1*qpd_max)
#
#        curve = createCurve(QtGui.QPen(QtCore.Qt.black),
#                            QtGui.QBrush(),
#                            7)
#        curve.setData(stage, qpd)
#        curve.attach(self.plot)
#        self.curves.append(curve)
#        self.plot.replot()
#
#        x_vals = numpy.array([-1.0, 1.0])
#        y_vals = (x_vals - offset)/slope
#
#        pen = QtGui.QPen(QtCore.Qt.black)
#        pen.setWidth(2)
#        curve = createCurve(pen,
#                            QtGui.QBrush(),
#                            0)
#        curve.setData(x_vals, y_vals)
#        curve.attach(self.plot)
#        self.curves.append(curve)
#
#        self.plot.setStaticText(QtGui.QStaticText("slope = {0:.3f} au/um".format(-1.0/slope)))
#
#        self.plot.replot()

    def plotWxWyData(self, wx, wy, cat):
        self.plot(wx, wy,
                  pen = None,
                  symbol = 'o',
                  symbolPen = QtGui.QPen(QtCore.Qt.red),
                  symbolBrush = QtGui.QBrush(QtCore.Qt.blue),
                  symbolSize = 3)

    def plotWxWyFit(self, wxfit, wyfit):
        a_pen = QtGui.QPen(QtCore.Qt.black)
        #a_pen.setWidth(2)
        self.plot(wxfit, wyfit, pen = a_pen)

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



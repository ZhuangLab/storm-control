#!/usr/bin/python
#
# Spot counter.
#
# Hazen 3/09
#

import sys
from PyQt4 import QtCore, QtGui
import sip

import halLib.parameters as params

# Debugging
import halLib.hdebug as hdebug

# UIs.
import qtdesigner.spotcounter_ui as spotCounterUi

# stage
import qtWidgets.qtSpotCounter as qtSpotCounter


#
# Spot Count Graphing Widget.
#
class QSpotGraph(QtGui.QWidget):
    def __init__(self, x_size, y_size, x_points, y_min, y_max, colors, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.x_size = x_size
        self.y_size = y_size
        self.y_min = float(y_min)
        self.y_max = float(y_max)
        self.colors = colors
        self.points_per_cycle = len(colors)
        self.x_scale = float(x_size)/float(x_points)
        self.cycle = 0
        if self.points_per_cycle > 1:
            self.cycle = self.x_scale * float(self.points_per_cycle)
        self.y_scale = float(y_size)/5.0
        self.range = y_max - y_min
        self.x_points = x_points
        self.data = []
        for i in range(self.x_points):
            self.data.append(0)

    def changeYRange(self, y_min = None, y_max = None):
        if y_min:
            self.y_min = y_min
        if y_max:
            self.y_max = y_max
        self.range = self.y_max - self.y_min

    def paintEvent(self, Event):
        painter = QtGui.QPainter(self)

        # Background
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)

        # Draw lines in y to denote the start of each cycle, but only
        # if we have at least 2 points per cycle.
        #
        # Draw grid lines in x.
        if self.cycle:
            painter.setPen(QtGui.QColor(200, 200, 200))
            x = 0.0
            while x < float(self.x_size):
                ix = int(x)
                painter.drawLine(ix, 0, ix, self.y_size)
                x += self.cycle

            y = 0.0
            while y < float(self.y_size):
                iy = int(y)
                painter.drawLine(0, iy, self.x_size, iy)
                y += self.y_scale

        if self.data:
            # Lines
            painter.setPen(QtGui.QColor(0, 0, 0))
            x1 = int(self.x_scale * float(0))
            y1 = self.y_size - int((self.data[0] - self.y_min)/self.range * float(self.y_size))
            for i in range(len(self.data)-1):
                x2 = int(self.x_scale * float(i+1))
                y2 = self.y_size - int((self.data[i+1] - self.y_min)/self.range * float(self.y_size))
                painter.drawLine(x1, y1, x2, y2)
                x1 = x2
                y1 = y2

            # Points
            for i in range(len(self.data)):
                color = self.colors[i % self.points_per_cycle]
                qtcolor = 0
                if color:
                    qtcolor = QtGui.QColor(color[0], color[1], color[2])
                else:
                    qtcolor = QtGui.QColor(0, 0, 0)
                painter.setPen(QtGui.QColor(0, 0, 0))
#                painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0),0))
                painter.setBrush(qtcolor)

                x = int(self.x_scale * float(i))
                y = self.y_size - int((self.data[i] - self.y_min)/self.range * float(self.y_size))
                if y < 0:
                    y = 0
                if y > self.y_size:
                    y = self.y_size
                painter.drawEllipse(x - 2, y - 2, 4, 4)

    def updateGraph(self, frame_index, spots):
        self.data[frame_index % self.x_points] = spots
        self.update()


#
# STORM image display widget.
#
class QImageGraph(QtGui.QWidget):
    def __init__(self, x_size, y_size, x_range, y_range, scale_bar_len, colors, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.x_size = x_size
        self.y_size = y_size
        self.x_scale = float(x_size)/float(x_range)
        self.y_scale = float(y_size)/float(y_range)
        self.scale_bar_len = int(round(scale_bar_len))
        self.buffer = QtGui.QPixmap(x_size, y_size)
        self.colors = colors
        self.points_per_cycle = len(colors)

    def blank(self):
        painter = QtGui.QPainter(self.buffer)
        color = QtGui.QColor(0, 0, 0)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.x_size, self.y_size)
        self.update()

    def paintEvent(self, Event):
        # draw the scale bar
        painter = QtGui.QPainter(self.buffer)
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.setBrush(QtGui.QColor(255, 255, 255))
        painter.drawRect(5, 5, 5 + self.scale_bar_len, 5)
            
        # transfer to display
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.buffer)

    def saveImage(self, filename):
        self.buffer.save(filename, "PNG", -1)

    def updateImage(self, index, x_locs, y_locs, spots):
        painter = QtGui.QPainter(self.buffer)
        color = self.colors[index % self.points_per_cycle]
        if color:
            qtcolor = QtGui.QColor(color[0], color[1], color[2], 5)
            painter.setPen(qtcolor)
            for i in range(spots):
                ix = int(self.x_scale * x_locs[i])
                iy = int(self.y_scale * y_locs[i])
                painter.drawPoint(ix, iy)
            self.update()
            

#
#
# Spot Counter Dialog Box
#
class SpotCounter(QtGui.QDialog):
    @hdebug.debug
    def __init__(self, parameters, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.debug = 1
        self.filming = 0
        self.filename = 0
        self.spots = 0
        self.spot_counter = 0
        self.spot_graph = 0
        self.image_graph = 0

        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        # UI setup
        self.ui = spotCounterUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Spot Counter")

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            #self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleOk)
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            #self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleQuit)
            self.ui.okButton.clicked.connect(self.handleQuit)
        #self.connect(self.ui.maxSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.handleMaxChange)
        self.ui.maxSpinBox.valueChanged.connect(self.handleMaxChange)
        #self.connect(self.ui.minSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.handleMinChange)
        self.ui.minSpinBox.valueChanged.connect(self.handleMinChange)

        # set modeless
        self.setModal(False)

    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    @hdebug.debug
    def handleMaxChange(self, new_max):
        self.spot_graph.changeYRange(y_max = new_max)
        self.ui.minSpinBox.setMaximum(new_max - 10)
        self.parameters.max_spots = new_max

    @hdebug.debug
    def handleMinChange(self, new_min):
        self.spot_graph.changeYRange(y_min = new_min)
        self.ui.maxSpinBox.setMinimum(new_min + 10)
        self.parameters.max_spots = new_min

    @hdebug.debug
    def handleOk(self):
        self.hide()

    @hdebug.debug
    def handleQuit(self):
        self.close()

    def newImageToCount(self, frame):
        if self.spot_counter:
            self.spot_counter.newImageToCount(frame)

    @hdebug.debug
    def newParameters(self, parameters, colors):
        if self.spot_counter:
            self.spot_counter.shutDown()
        self.debug = parameters.debug
        self.parameters = parameters

        if self.spot_graph:
            sip.delete(self.spot_graph)
            sip.delete(self.image_graph)

        points_per_cycle = len(colors)
        total_points = points_per_cycle
        while total_points < 100:
            total_points += points_per_cycle

        # spot counts graph
        graph_w = self.ui.graphFrame.width() - 4
        graph_h = self.ui.graphFrame.height() - 4
        self.spot_graph = QSpotGraph(graph_w,
                                     graph_h,
                                     total_points,
                                     parameters.min_spots,
                                     parameters.max_spots,
                                     colors,
                                     parent = self.ui.graphFrame)
        self.spot_graph.setGeometry(2, 2, graph_w, graph_h)
        self.spot_graph.show()

        # STORM image
        image_w = self.ui.imageFrame.width() - 4
        image_h = self.ui.imageFrame.height() - 4
        scale_bar_len = (parameters.scale_bar_len / parameters.nm_per_pixel) * \
            float(image_w) / float(parameters.x_pixels * parameters.x_bin)
        self.image_graph = QImageGraph(image_w,
                                       image_h,
                                       parameters.x_pixels / parameters.x_bin,
                                       parameters.y_pixels / parameters.y_bin,
                                       scale_bar_len,
                                       colors,
                                       parent = self.ui.imageFrame)
        self.image_graph.setGeometry(2, 2, image_w, image_h)
        self.image_graph.blank()
        self.image_graph.show()

        # The spot counter
        self.spot_counter = qtSpotCounter.QObjectCounter(parameters)
        self.connect(self.spot_counter, QtCore.SIGNAL("imageProcessed(int, int)"), self.update)

        # UI update
        self.ui.maxSpinBox.setValue(parameters.max_spots)
        self.ui.minSpinBox.setValue(parameters.min_spots)
        self.ui.countsLabel1.setText("0")
        self.ui.countsLabel2.setText("0")

    def update(self, thread_index, frame_index):
        [x_locs, y_locs, spots] = self.spot_counter.getResults(thread_index)
        self.spots += spots
        self.spot_graph.updateGraph(frame_index, spots)
        if self.filming:
            self.ui.countsLabel1.setText(str(self.spots))
            self.ui.countsLabel2.setText(str(self.spots))
            self.image_graph.updateImage(frame_index, x_locs, y_locs, spots)

    @hdebug.debug        
    def quit(self):
        pass

    @hdebug.debug
    def shutDown(self):
        if self.spot_counter:
            self.spot_counter.shutDown()

    @hdebug.debug
    def startCounter(self, name):
        if self.spot_counter:
            self.spot_counter.reset()
            self.image_graph.blank()
            self.spots = 0
            self.filming = 1
            self.filename = 0
            if name:
                self.filename = name + ".png"

    @hdebug.debug
    def stopCounter(self):
        self.spots = 0
        self.filming = 0
        if self.filename:
            self.image_graph.saveImage(self.filename)


#
# testing
#

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    parameters = params.Parameters("settings_default.xml")
    spotCounter = SpotCounter(parameters)
    spotCounter.show()
    app.exec_()


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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


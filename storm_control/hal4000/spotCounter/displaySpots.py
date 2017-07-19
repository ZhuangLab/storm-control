#!/usr/bin/env python
"""
These classes render the graph / image for the spot
counter.

Hazen 05/17
"""
import numpy

from PyQt5 import QtGui, QtWidgets


class SpotWidget(QtWidgets.QWidget):
    """
    Spot graph / display base class.
    """
    def __init__(self, shutters_info = None, **kwds):
        super().__init__(**kwds)

        if shutters_info is None:
            self.colors = [None]
            self.cycle_length = 1
        else:
            self.setShuttersInfo(shutters_info)

    def setShuttersInfo(self, shutters_info):
        self.colors = shutters_info.getColorData()
        self.cycle_length = shutters_info.getFrames()


class SpotGraph(SpotWidget):
    """
    The spot graph for a camera feed.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
            
        self.x_points = 100
        self.y_max = 500.0

        self.data = numpy.zeros(self.x_points, dtype = numpy.uint16)
        self.delta_x = float(self.width())/float(self.x_points-1)
        self.delta_y = float(self.height())/5.0

    def clearGraph(self):
        self.data = numpy.zeros(self.x_points, dtype = numpy.uint16)
        self.update()
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        # White background.
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())

        #
        # Grid Lines.
        #
        # Draw lines in y to denote the start of each cycle, but only
        # if we have at least 2 points per cycle.
        #
        # Draw grid lines in x.
        #
        painter.setPen(QtGui.QColor(200, 200, 200))
        if (self.cycle_length > 1):
            x = 0.0
            while x < float(self.width()):
                ix = int(x)
                painter.drawLine(ix, 0, ix, self.height())
                x += self.delta_x * self.cycle_length

        y = 0.0
        while y < float(self.height()):
            iy = int(y)
            painter.drawLine(0, iy, self.width(), iy)

            y += self.delta_y

        #
        # Plot the data.
        #
        
        # Lines
        painter.setPen(QtGui.QColor(0, 0, 0))
        x1 = 0
        y1 = self.height() - int(self.data[0]/self.y_max * self.height())
        for i in range(self.data.size - 1):
            x2 = int(self.delta_x * float(i+1))
            y2 = self.height() - int(self.data[i+1]/self.y_max * self.height())
            painter.drawLine(x1, y1, x2, y2)
            x1 = x2
            y1 = y2

        # Points
        for i in range(self.data.size):
            color = self.colors[i % self.cycle_length]
            if color is None:
                qt_color = QtGui.QColor(255, 255, 255)
            else:
                qt_color = QtGui.QColor(*color)
            painter.setPen(QtGui.QColor(0, 0, 0))
            painter.setBrush(qt_color)

            x = int(self.delta_x * float(i))
            y = self.height() - int(self.data[i]/self.y_max * self.height())
            painter.drawEllipse(x - 2, y - 2, 4, 4)

    def resizeEvent(self, event):
        self.delta_x = float(self.width())/float(self.x_points-1)
        self.delta_y = float(self.height())/5.0
        self.update()
        
    def setMaxSpots(self, max_spots):
        self.y_max = float(max_spots)
        self.update()

    def updatePoint(self, frame_number, counts):
        self.data[frame_number%self.x_points] = counts
        self.update()

        
class SpotPicture(SpotWidget):

    def __init__(self,
                 camera_fn = None,
                 pixel_size = None,
                 scale_bar_len = None,
                 **kwds):
        super().__init__(**kwds)
        
        self.scale_bar_len = int(round(1.0e-3 * scale_bar_len/pixel_size))

        self.scale = 2.0  # Fixed for now, but possibly something we can change.

        # The final image size in pixels.
        xp = int(self.scale * camera_fn.getParameter("x_pixels"))
        yp = int(self.scale * camera_fn.getParameter("y_pixels"))

        # For rendering an intermediate picture.
        self.q_pixmap = QtGui.QPixmap(xp, yp)

        # Figure out transform matrix.
        #
        # FIXME: Duplicated from qtWidgets.qtCameraGraphicsView
        #
        if camera_fn.getParameter("flip_horizontal"):
            flip_lr = QtGui.QTransform(-1.0, 0.0, 0.0,
                                       0.0, 1.0, 0.0,
                                       xp, 0.0, 1.0)
        else:
            flip_lr = QtGui.QTransform()

        if camera_fn.getParameter("flip_vertical"):
            flip_ud = QtGui.QTransform(1.0, 0.0, 0.0,
                                       0.0, -1.0, 0.0,
                                       0.0, yp, 1.0)
        else:
            flip_ud = QtGui.QTransform()

        if camera_fn.getParameter("transpose"):
            flip_xy = QtGui.QTransform(0.0, 1.0, 0.0,
                                       1.0, 0.0, 0.0,
                                       0.0, 0.0, 1.0)
        else:
            flip_xy = QtGui.QTransform()            

        self.transform = flip_lr * flip_ud * flip_xy
        
        self.setFixedSize(xp, yp)

    def clearPicture(self):
        painter = QtGui.QPainter(self.q_pixmap)
        color = QtGui.QColor(0,0,0)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0,0,self.q_pixmap.width(),self.q_pixmap.height())
        self.update()

    def paintEvent(self, event):

        # Transfer to display.
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.q_pixmap)
        
        # Draw the scale bar.
        painter.setPen(QtGui.QColor(255,255,255))
        painter.setBrush(QtGui.QColor(255,255,255))
        painter.drawRect(5, 5, 5 + self.scale_bar_len, 5)

    def savePicture(self, filename):
        self.q_pixmap.save(filename + ".png", "PNG", -1)
        
    def updateImage(self, frame_number, locs):

        # Figure out color. If it is None we don't draw anything.
        color = self.colors[frame_number % self.cycle_length]
        if color is None:
            return
        
        x = numpy.round(self.scale*locs[0])
        y = numpy.round(self.scale*locs[1])

        painter = QtGui.QPainter(self.q_pixmap)
        painter.setTransform(self.transform)
        painter.setPen(QtGui.QColor(*color))
        
        for i in range(x.size):
            painter.drawPoint(int(x[i]),
                              int(y[i]))
        self.update()

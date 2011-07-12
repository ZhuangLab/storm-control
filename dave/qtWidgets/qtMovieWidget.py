#!/usr/bin/python
#
# Qt Widget for handling the display of movie data.
#
# Hazen 6/09
#

from PyQt4 import QtCore, QtGui

# Camera widget
class QMovieWidget(QtGui.QWidget):
    def __init__(self, debug = 1, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.debug = debug
        self.movie_index = None
        self.number_movies = None
        self.movie = None

    def updateDisplay(self, movie_index, number_movies, current_movie):
        if self.debug:
            print " updateDisplay"
        self.movie_index = movie_index
        self.number_movies = number_movies
        self.movie = current_movie
        self.update()
        
    def paintEvent(self, Event):
        if self.debug:
            print " paintEvent"
        painter = QtGui.QPainter(self)

        # Background
        color = QtGui.QColor(255, 255, 255)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(0, 0, self.width(), self.height())
        
        # Info
        painter.setPen(QtGui.QColor(0,0,0))
        if self.number_movies:
            y = 14
            line_inc = 10
            painter.drawText(4, y, "Movie: %d (%d)" % (self.movie_index, self.number_movies))
            y += line_inc
            painter.drawText(4, y

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

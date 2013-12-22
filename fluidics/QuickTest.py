import sys
from PyQt4 import QtGui, QtCore
from ui_qt_valve import QtValveControlWidget

class Stack(QtValveControlWidget):
    def __init__(self, parent=None):
        QtValveControlWidget.__init__(self, parent)

class Window(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.stack = Stack(self)
        self.setCentralWidget(self.stack)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()    

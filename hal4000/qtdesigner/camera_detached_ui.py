# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'camera-detached.ui'
#
# Created: Sat Sep 19 21:02:02 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(586, 619)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(0, 0))
        Dialog.setMaximumSize(QtCore.QSize(10000, 10000))
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.cameraFrame = QtGui.QFrame(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cameraFrame.sizePolicy().hasHeightForWidth())
        self.cameraFrame.setSizePolicy(sizePolicy)
        self.cameraFrame.setMinimumSize(QtCore.QSize(585, 543))
        self.cameraFrame.setMaximumSize(QtCore.QSize(10000, 10000))
        self.cameraFrame.setFrameShape(QtGui.QFrame.Box)
        self.cameraFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.cameraFrame.setObjectName(_fromUtf8("cameraFrame"))
        self.verticalLayout.addWidget(self.cameraFrame)
        self.widget = QtGui.QWidget(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMaximumSize(QtCore.QSize(16777215, 75))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setMargin(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.cameraParamsFrame = QtGui.QFrame(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cameraParamsFrame.sizePolicy().hasHeightForWidth())
        self.cameraParamsFrame.setSizePolicy(sizePolicy)
        self.cameraParamsFrame.setMinimumSize(QtCore.QSize(0, 0))
        self.cameraParamsFrame.setMaximumSize(QtCore.QSize(16777215, 1000))
        self.cameraParamsFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.cameraParamsFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.cameraParamsFrame.setObjectName(_fromUtf8("cameraParamsFrame"))
        self.horizontalLayout.addWidget(self.cameraParamsFrame)
        self.widget_3 = QtGui.QWidget(self.widget)
        self.widget_3.setMinimumSize(QtCore.QSize(100, 0))
        self.widget_3.setMaximumSize(QtCore.QSize(16777215, 92))
        self.widget_3.setObjectName(_fromUtf8("widget_3"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.widget_3)
        self.verticalLayout_2.setMargin(2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        spacerItem = QtGui.QSpacerItem(20, 38, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.okButton = QtGui.QPushButton(self.widget_3)
        self.okButton.setMaximumSize(QtCore.QSize(100, 16777215))
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.verticalLayout_2.addWidget(self.okButton)
        self.horizontalLayout.addWidget(self.widget_3)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.okButton.setText(_translate("Dialog", "Close", None))


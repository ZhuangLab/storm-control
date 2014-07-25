# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'holoeye.ui'
#
# Created: Fri Jul 25 14:51:57 2014
#      by: PyQt4 UI code generator 4.9.6
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
        Dialog.resize(630, 365)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(630, 365))
        Dialog.setMaximumSize(QtCore.QSize(630, 365))
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.thumbnailWidget = HoloeyeThumbnail(Dialog)
        self.thumbnailWidget.setMinimumSize(QtCore.QSize(300, 300))
        self.thumbnailWidget.setMaximumSize(QtCore.QSize(800, 300))
        self.thumbnailWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.thumbnailWidget.setObjectName(_fromUtf8("thumbnailWidget"))
        self.horizontalLayout_2.addWidget(self.thumbnailWidget)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.patternComboBox = QtGui.QComboBox(Dialog)
        self.patternComboBox.setObjectName(_fromUtf8("patternComboBox"))
        self.horizontalLayout.addWidget(self.patternComboBox)
        self.periodDoubleSpinBox = QtGui.QDoubleSpinBox(Dialog)
        self.periodDoubleSpinBox.setMinimumSize(QtCore.QSize(80, 0))
        self.periodDoubleSpinBox.setDecimals(3)
        self.periodDoubleSpinBox.setMaximum(2.0)
        self.periodDoubleSpinBox.setSingleStep(0.01)
        self.periodDoubleSpinBox.setProperty("value", 0.1)
        self.periodDoubleSpinBox.setObjectName(_fromUtf8("periodDoubleSpinBox"))
        self.horizontalLayout.addWidget(self.periodDoubleSpinBox)
        self.screenLabel = QtGui.QLabel(Dialog)
        self.screenLabel.setObjectName(_fromUtf8("screenLabel"))
        self.horizontalLayout.addWidget(self.screenLabel)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Holoeye Control", None))
        self.screenLabel.setText(_translate("Dialog", "TextLabel", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))

from sc_hardware.holoeye.holoeyeThumbnail import HoloeyeThumbnail

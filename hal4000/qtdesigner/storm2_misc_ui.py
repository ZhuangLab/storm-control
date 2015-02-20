# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'storm2-misc.ui'
#
# Created: Fri Feb 20 16:07:45 2015
#      by: PyQt4 UI code generator 4.11.1
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
        Dialog.resize(391, 201)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(391, 201))
        Dialog.setMaximumSize(QtCore.QSize(391, 201))
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(300, 170, 75, 24))
        self.okButton.setCheckable(False)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.filterWheelGroupBox = QtGui.QGroupBox(Dialog)
        self.filterWheelGroupBox.setGeometry(QtCore.QRect(10, 110, 371, 51))
        self.filterWheelGroupBox.setObjectName(_fromUtf8("filterWheelGroupBox"))
        self.filter1Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter1Button.setGeometry(QtCore.QRect(10, 20, 51, 24))
        self.filter1Button.setCheckable(True)
        self.filter1Button.setAutoExclusive(True)
        self.filter1Button.setObjectName(_fromUtf8("filter1Button"))
        self.filter2Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter2Button.setGeometry(QtCore.QRect(70, 20, 51, 24))
        self.filter2Button.setCheckable(True)
        self.filter2Button.setAutoExclusive(True)
        self.filter2Button.setObjectName(_fromUtf8("filter2Button"))
        self.filter3Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter3Button.setGeometry(QtCore.QRect(130, 20, 51, 24))
        self.filter3Button.setCheckable(True)
        self.filter3Button.setAutoExclusive(True)
        self.filter3Button.setObjectName(_fromUtf8("filter3Button"))
        self.filter4Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter4Button.setGeometry(QtCore.QRect(190, 20, 51, 24))
        self.filter4Button.setCheckable(True)
        self.filter4Button.setAutoExclusive(True)
        self.filter4Button.setObjectName(_fromUtf8("filter4Button"))
        self.filter5Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter5Button.setGeometry(QtCore.QRect(250, 20, 51, 24))
        self.filter5Button.setCheckable(True)
        self.filter5Button.setAutoExclusive(True)
        self.filter5Button.setObjectName(_fromUtf8("filter5Button"))
        self.filter6Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter6Button.setGeometry(QtCore.QRect(310, 20, 51, 24))
        self.filter6Button.setCheckable(True)
        self.filter6Button.setAutoExclusive(True)
        self.filter6Button.setObjectName(_fromUtf8("filter6Button"))
        self.emGroupBox = QtGui.QGroupBox(Dialog)
        self.emGroupBox.setGeometry(QtCore.QRect(10, 20, 371, 81))
        self.emGroupBox.setObjectName(_fromUtf8("emGroupBox"))
        self.emFilter1Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter1Button.setGeometry(QtCore.QRect(10, 20, 51, 24))
        self.emFilter1Button.setCheckable(True)
        self.emFilter1Button.setAutoExclusive(True)
        self.emFilter1Button.setObjectName(_fromUtf8("emFilter1Button"))
        self.emFilter2Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter2Button.setGeometry(QtCore.QRect(70, 20, 51, 24))
        self.emFilter2Button.setCheckable(True)
        self.emFilter2Button.setAutoExclusive(True)
        self.emFilter2Button.setObjectName(_fromUtf8("emFilter2Button"))
        self.emFilter3Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter3Button.setGeometry(QtCore.QRect(130, 20, 51, 24))
        self.emFilter3Button.setCheckable(True)
        self.emFilter3Button.setAutoExclusive(True)
        self.emFilter3Button.setObjectName(_fromUtf8("emFilter3Button"))
        self.emFilter4Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter4Button.setGeometry(QtCore.QRect(190, 20, 51, 24))
        self.emFilter4Button.setCheckable(True)
        self.emFilter4Button.setAutoExclusive(True)
        self.emFilter4Button.setObjectName(_fromUtf8("emFilter4Button"))
        self.emFilter6Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter6Button.setGeometry(QtCore.QRect(310, 20, 51, 24))
        self.emFilter6Button.setCheckable(True)
        self.emFilter6Button.setAutoExclusive(True)
        self.emFilter6Button.setObjectName(_fromUtf8("emFilter6Button"))
        self.emFilter5Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter5Button.setGeometry(QtCore.QRect(250, 20, 51, 24))
        self.emFilter5Button.setCheckable(True)
        self.emFilter5Button.setAutoExclusive(True)
        self.emFilter5Button.setObjectName(_fromUtf8("emFilter5Button"))
        self.emCheckBox = QtGui.QCheckBox(self.emGroupBox)
        self.emCheckBox.setGeometry(QtCore.QRect(12, 52, 131, 17))
        self.emCheckBox.setObjectName(_fromUtf8("emCheckBox"))
        self.emSpinBox = QtGui.QSpinBox(self.emGroupBox)
        self.emSpinBox.setGeometry(QtCore.QRect(290, 50, 71, 22))
        self.emSpinBox.setMinimum(1)
        self.emSpinBox.setMaximum(1000)
        self.emSpinBox.setObjectName(_fromUtf8("emSpinBox"))
        self.emLabel = QtGui.QLabel(self.emGroupBox)
        self.emLabel.setGeometry(QtCore.QRect(201, 51, 81, 20))
        self.emLabel.setObjectName(_fromUtf8("emLabel"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Miscellaneous Controls", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))
        self.filterWheelGroupBox.setTitle(_translate("Dialog", "Turret Filter Wheel Control", None))
        self.filter1Button.setText(_translate("Dialog", "1", None))
        self.filter2Button.setText(_translate("Dialog", "2", None))
        self.filter3Button.setText(_translate("Dialog", "3", None))
        self.filter4Button.setText(_translate("Dialog", "4", None))
        self.filter5Button.setText(_translate("Dialog", "5", None))
        self.filter6Button.setText(_translate("Dialog", "6", None))
        self.emGroupBox.setTitle(_translate("Dialog", "Emission Filter Wheen Control", None))
        self.emFilter1Button.setText(_translate("Dialog", "1", None))
        self.emFilter2Button.setText(_translate("Dialog", "2", None))
        self.emFilter3Button.setText(_translate("Dialog", "3", None))
        self.emFilter4Button.setText(_translate("Dialog", "4", None))
        self.emFilter6Button.setText(_translate("Dialog", "6", None))
        self.emFilter5Button.setText(_translate("Dialog", "5", None))
        self.emCheckBox.setText(_translate("Dialog", "Move During Filming", None))
        self.emLabel.setText(_translate("Dialog", "Period (frames)", None))


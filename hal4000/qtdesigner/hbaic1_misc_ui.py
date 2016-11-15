# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hbaic1-misc.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
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
        Dialog.resize(390, 140)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(390, 140))
        Dialog.setMaximumSize(QtCore.QSize(520, 140))
        self.verticalLayout_2 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.emGroupBox = QtGui.QGroupBox(Dialog)
        self.emGroupBox.setObjectName(_fromUtf8("emGroupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.emGroupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.emFilter1Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter1Button.setCheckable(True)
        self.emFilter1Button.setAutoExclusive(True)
        self.emFilter1Button.setObjectName(_fromUtf8("emFilter1Button"))
        self.horizontalLayout_2.addWidget(self.emFilter1Button)
        self.emFilter2Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter2Button.setCheckable(True)
        self.emFilter2Button.setAutoExclusive(True)
        self.emFilter2Button.setObjectName(_fromUtf8("emFilter2Button"))
        self.horizontalLayout_2.addWidget(self.emFilter2Button)
        self.emFilter3Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter3Button.setCheckable(True)
        self.emFilter3Button.setAutoExclusive(True)
        self.emFilter3Button.setObjectName(_fromUtf8("emFilter3Button"))
        self.horizontalLayout_2.addWidget(self.emFilter3Button)
        self.emFilter4Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter4Button.setCheckable(True)
        self.emFilter4Button.setAutoExclusive(True)
        self.emFilter4Button.setObjectName(_fromUtf8("emFilter4Button"))
        self.horizontalLayout_2.addWidget(self.emFilter4Button)
        self.emFilter5Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter5Button.setCheckable(True)
        self.emFilter5Button.setAutoExclusive(True)
        self.emFilter5Button.setObjectName(_fromUtf8("emFilter5Button"))
        self.horizontalLayout_2.addWidget(self.emFilter5Button)
        self.emFilter6Button = QtGui.QPushButton(self.emGroupBox)
        self.emFilter6Button.setCheckable(True)
        self.emFilter6Button.setAutoExclusive(True)
        self.emFilter6Button.setObjectName(_fromUtf8("emFilter6Button"))
        self.horizontalLayout_2.addWidget(self.emFilter6Button)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.emCheckBox = QtGui.QCheckBox(self.emGroupBox)
        self.emCheckBox.setObjectName(_fromUtf8("emCheckBox"))
        self.horizontalLayout.addWidget(self.emCheckBox)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.emLabel = QtGui.QLabel(self.emGroupBox)
        self.emLabel.setObjectName(_fromUtf8("emLabel"))
        self.horizontalLayout.addWidget(self.emLabel)
        self.emSpinBox = QtGui.QSpinBox(self.emGroupBox)
        self.emSpinBox.setMinimum(1)
        self.emSpinBox.setMaximum(1000)
        self.emSpinBox.setObjectName(_fromUtf8("emSpinBox"))
        self.horizontalLayout.addWidget(self.emSpinBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addWidget(self.emGroupBox)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setCheckable(False)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout_3.addWidget(self.okButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Miscellaneous Controls", None))
        self.emGroupBox.setTitle(_translate("Dialog", "Emission Filter Wheel Control", None))
        self.emFilter1Button.setText(_translate("Dialog", "1", None))
        self.emFilter2Button.setText(_translate("Dialog", "2", None))
        self.emFilter3Button.setText(_translate("Dialog", "3", None))
        self.emFilter4Button.setText(_translate("Dialog", "4", None))
        self.emFilter5Button.setText(_translate("Dialog", "5", None))
        self.emFilter6Button.setText(_translate("Dialog", "6", None))
        self.emCheckBox.setText(_translate("Dialog", "Move During Filming", None))
        self.emLabel.setText(_translate("Dialog", "Period (frames)", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))


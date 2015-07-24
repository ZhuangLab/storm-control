# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mosaic_dialog.ui'
#
# Created: Thu Jul 16 16:29:55 2015
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
        Dialog.resize(437, 223)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(437, 223))
        Dialog.setMaximumSize(QtCore.QSize(437, 225))
        self.verticalLayout_3 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.groupBox = QtGui.QGroupBox(Dialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.pixLabel = QtGui.QLabel(self.groupBox)
        self.pixLabel.setObjectName(_fromUtf8("pixLabel"))
        self.horizontalLayout_7.addWidget(self.pixLabel)
        self.pixDoubleSpinBox = QtGui.QDoubleSpinBox(self.groupBox)
        self.pixDoubleSpinBox.setDecimals(3)
        self.pixDoubleSpinBox.setMaximum(10.0)
        self.pixDoubleSpinBox.setSingleStep(0.01)
        self.pixDoubleSpinBox.setProperty("value", 0.16)
        self.pixDoubleSpinBox.setObjectName(_fromUtf8("pixDoubleSpinBox"))
        self.horizontalLayout_7.addWidget(self.pixDoubleSpinBox)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.horizCheckBox = QtGui.QCheckBox(self.groupBox)
        self.horizCheckBox.setObjectName(_fromUtf8("horizCheckBox"))
        self.verticalLayout.addWidget(self.horizCheckBox)
        self.vertCheckBox = QtGui.QCheckBox(self.groupBox)
        self.vertCheckBox.setObjectName(_fromUtf8("vertCheckBox"))
        self.verticalLayout.addWidget(self.vertCheckBox)
        self.transCheckBox = QtGui.QCheckBox(self.groupBox)
        self.transCheckBox.setObjectName(_fromUtf8("transCheckBox"))
        self.verticalLayout.addWidget(self.transCheckBox)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_5.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(Dialog)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.objectiveLabel = QtGui.QLabel(self.groupBox_2)
        self.objectiveLabel.setObjectName(_fromUtf8("objectiveLabel"))
        self.horizontalLayout.addWidget(self.objectiveLabel)
        self.objectiveLineEdit = QtGui.QLineEdit(self.groupBox_2)
        self.objectiveLineEdit.setMaximumSize(QtCore.QSize(80, 16777215))
        self.objectiveLineEdit.setObjectName(_fromUtf8("objectiveLineEdit"))
        self.horizontalLayout.addWidget(self.objectiveLineEdit)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.magLabel = QtGui.QLabel(self.groupBox_2)
        self.magLabel.setObjectName(_fromUtf8("magLabel"))
        self.horizontalLayout_2.addWidget(self.magLabel)
        self.magDoubleSpinBox = QtGui.QDoubleSpinBox(self.groupBox_2)
        self.magDoubleSpinBox.setMinimum(1.0)
        self.magDoubleSpinBox.setMaximum(200.0)
        self.magDoubleSpinBox.setSingleStep(0.01)
        self.magDoubleSpinBox.setProperty("value", 100.0)
        self.magDoubleSpinBox.setObjectName(_fromUtf8("magDoubleSpinBox"))
        self.horizontalLayout_2.addWidget(self.magDoubleSpinBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.xoffLabel = QtGui.QLabel(self.groupBox_2)
        self.xoffLabel.setObjectName(_fromUtf8("xoffLabel"))
        self.horizontalLayout_3.addWidget(self.xoffLabel)
        self.xoffDoubleSpinBox = QtGui.QDoubleSpinBox(self.groupBox_2)
        self.xoffDoubleSpinBox.setMinimum(-10000.0)
        self.xoffDoubleSpinBox.setMaximum(10000.0)
        self.xoffDoubleSpinBox.setObjectName(_fromUtf8("xoffDoubleSpinBox"))
        self.horizontalLayout_3.addWidget(self.xoffDoubleSpinBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.yoffLabel = QtGui.QLabel(self.groupBox_2)
        self.yoffLabel.setObjectName(_fromUtf8("yoffLabel"))
        self.horizontalLayout_4.addWidget(self.yoffLabel)
        self.yoffDoubleSpinBox = QtGui.QDoubleSpinBox(self.groupBox_2)
        self.yoffDoubleSpinBox.setMinimum(-10000.0)
        self.yoffDoubleSpinBox.setMaximum(10000.0)
        self.yoffDoubleSpinBox.setObjectName(_fromUtf8("yoffDoubleSpinBox"))
        self.horizontalLayout_4.addWidget(self.yoffDoubleSpinBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5.addWidget(self.groupBox_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem1)
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout_6.addWidget(self.okButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Mosaic Dialog", None))
        self.groupBox.setTitle(_translate("Dialog", "Mosaic", None))
        self.pixLabel.setText(_translate("Dialog", "um per pixel", None))
        self.horizCheckBox.setText(_translate("Dialog", "Flip Horiztonal", None))
        self.vertCheckBox.setText(_translate("Dialog", "Flip Vertical", None))
        self.transCheckBox.setText(_translate("Dialog", "Transpose", None))
        self.groupBox_2.setTitle(_translate("Dialog", "Objective", None))
        self.objectiveLabel.setText(_translate("Dialog", "Objective", None))
        self.objectiveLineEdit.setText(_translate("Dialog", "100x", None))
        self.magLabel.setText(_translate("Dialog", "Magnification", None))
        self.xoffLabel.setText(_translate("Dialog", "X Offset", None))
        self.yoffLabel.setText(_translate("Dialog", "Y Offset", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))


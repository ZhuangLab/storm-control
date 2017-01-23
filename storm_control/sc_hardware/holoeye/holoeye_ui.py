# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'holoeye.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(630, 365)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(630, 365))
        Dialog.setMaximumSize(QtCore.QSize(630, 365))
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.thumbnailWidget = HoloeyeThumbnail(Dialog)
        self.thumbnailWidget.setMinimumSize(QtCore.QSize(300, 300))
        self.thumbnailWidget.setMaximumSize(QtCore.QSize(800, 300))
        self.thumbnailWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.thumbnailWidget.setObjectName("thumbnailWidget")
        self.horizontalLayout_2.addWidget(self.thumbnailWidget)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.patternComboBox = QtWidgets.QComboBox(Dialog)
        self.patternComboBox.setObjectName("patternComboBox")
        self.horizontalLayout.addWidget(self.patternComboBox)
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setMinimumSize(QtCore.QSize(80, 0))
        self.widget.setObjectName("widget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.periodDoubleSpinBox = QtWidgets.QDoubleSpinBox(self.widget)
        self.periodDoubleSpinBox.setMinimumSize(QtCore.QSize(80, 0))
        self.periodDoubleSpinBox.setDecimals(4)
        self.periodDoubleSpinBox.setMaximum(2.0)
        self.periodDoubleSpinBox.setSingleStep(0.001)
        self.periodDoubleSpinBox.setProperty("value", 0.01)
        self.periodDoubleSpinBox.setObjectName("periodDoubleSpinBox")
        self.horizontalLayout_3.addWidget(self.periodDoubleSpinBox)
        self.horizontalLayout.addWidget(self.widget)
        self.screenLabel = QtWidgets.QLabel(Dialog)
        self.screenLabel.setObjectName("screenLabel")
        self.horizontalLayout.addWidget(self.screenLabel)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Holoeye Control"))
        self.screenLabel.setText(_translate("Dialog", "TextLabel"))
        self.okButton.setText(_translate("Dialog", "Ok"))

from sc_hardware.holoeye.holoeyeThumbnail import HoloeyeThumbnail

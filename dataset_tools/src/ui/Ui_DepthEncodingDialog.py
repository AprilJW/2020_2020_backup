# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DepthEncodingDialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DepthEncodingDialog(object):
    def setupUi(self, DepthEncodingDialog):
        DepthEncodingDialog.setObjectName("DepthEncodingDialog")
        DepthEncodingDialog.resize(346, 250)
        self.widget = QtWidgets.QWidget(DepthEncodingDialog)
        self.widget.setGeometry(QtCore.QRect(10, 0, 331, 250))
        self.widget.setObjectName("widget")
        self.start_depth_encoding = QtWidgets.QPushButton(self.widget)
        self.start_depth_encoding.setGeometry(QtCore.QRect(90, 195, 137, 22))
        self.start_depth_encoding.setObjectName("start_depth_encoding")
        self.depth_source_type = QtWidgets.QComboBox(self.widget)
        self.depth_source_type.setGeometry(QtCore.QRect(190, 20, 131, 22))
        self.depth_source_type.setObjectName("depth_source_type")
        self.depth_source_type.addItem("")
        self.depth_source_type.addItem("")
        self.depth_source_type.addItem("")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setGeometry(QtCore.QRect(10, 20, 131, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setGeometry(QtCore.QRect(10, 60, 121, 16))
        self.label_2.setObjectName("label_2")
        self.depth_encoding_type = QtWidgets.QComboBox(self.widget)
        self.depth_encoding_type.setGeometry(QtCore.QRect(190, 60, 131, 22))
        self.depth_encoding_type.setObjectName("depth_encoding_type")
        self.depth_encoding_type.addItem("")
        self.depth_encoding_type.addItem("")
        self.depth_encoding_type.addItem("")
        self.depth_encoding_type.addItem("")
        self.encoding_min_label = QtWidgets.QLabel(self.widget)
        self.encoding_min_label.setText("Encoding Min")
        self.encoding_min_label.setGeometry(QtCore.QRect(10, 100, 121, 22))
        self.encoding_max_label = QtWidgets.QLabel(self.widget)
        self.encoding_max_label.setText("Encoding Max")
        self.encoding_max_label.setGeometry(QtCore.QRect(10, 140, 121, 22))
        self.depth_encoding_min = QtWidgets.QSpinBox(self.widget)
        self.depth_encoding_min.setRange(-1000000, 1000000)
        self.depth_encoding_min.setValue(-1)
        self.depth_encoding_min.setGeometry(QtCore.QRect(190, 98, 50, 22))
        self.depth_encoding_max = QtWidgets.QSpinBox(self.widget)
        self.depth_encoding_max.setRange(-1000000, 1000000)
        self.depth_encoding_max.setValue(-1)
        self.depth_encoding_max.setGeometry(QtCore.QRect(190, 136, 50, 22))

        self.retranslateUi(DepthEncodingDialog)
        self.depth_source_type.setCurrentIndex(1)
        self.depth_encoding_type.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(DepthEncodingDialog)

    def retranslateUi(self, DepthEncodingDialog):
        _translate = QtCore.QCoreApplication.translate
        DepthEncodingDialog.setWindowTitle(_translate("DepthEncodingDialog", "Data Format"))
        self.start_depth_encoding.setText(_translate("DepthEncodingDialog", "Start Depth Encoding"))
        self.depth_source_type.setItemText(0, _translate("DepthEncodingDialog", "None"))
        self.depth_source_type.setItemText(1, _translate("DepthEncodingDialog", "EXR"))
        self.depth_source_type.setItemText(2, _translate("DepthEncodingDialog", "IMAGE"))
        self.label.setText(_translate("DepthEncodingDialog", "Depth Source Type:"))
        self.label_2.setText(_translate("DepthEncodingDialog", "Encoding Type"))
        self.depth_encoding_type.setItemText(0, _translate("DepthEncodingDialog", "None"))
        self.depth_encoding_type.setItemText(1, _translate("DepthEncodingDialog", "Jet Mapping"))
        self.depth_encoding_type.setItemText(2, _translate("DepthEncodingDialog", "Surface Normal"))
        self.depth_encoding_type.setItemText(3, _translate("DepthEncodingDialog", "HHA"))


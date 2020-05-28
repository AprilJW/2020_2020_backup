from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.Qt import pyqtSlot

class RGBWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(QtWidgets.QWidget, self).__init__()
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        self.label.setText("R: ")
        self.horizontalLayout.addWidget(self.label)
        self.red = QtWidgets.QSpinBox(self)
        self.red.setMaximum(256)
        self.red.setObjectName("red")
        self.horizontalLayout.addWidget(self.red)
        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setText("G: ")
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.green = QtWidgets.QSpinBox(self)
        self.green.setMaximum(256)
        self.green.setObjectName("green")
        self.horizontalLayout.addWidget(self.green)
        self.label_5 = QtWidgets.QLabel(self)
        self.label_5.setText("B: ")
        self.label_5.setObjectName("label_5")
        self.horizontalLayout.addWidget(self.label_5)
        self.blue = QtWidgets.QSpinBox(self)
        self.blue.setMaximum(256)
        self.blue.setObjectName("blue")
        self.horizontalLayout.addWidget(self.blue)
        QtCore.QMetaObject.connectSlotsByName(self)

    def setValue(self, r, g, b):
        self.red.setValue(r)
        self.green.setValue(g)
        self.blue.setValue(b)
        
    def value(self):
        return (self.red.value(), self.green.value(), self.blue.value())



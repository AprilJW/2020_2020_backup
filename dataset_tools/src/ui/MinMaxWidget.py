from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class MinMaxWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__()
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.min = QSpinBox(self)
        self.min.setObjectName("min")
        self.min.setMinimum(-99)
        self.min.setValue(-10)
        self.horizontalLayout.addWidget(self.min)
        self.max = QSpinBox(self)
        self.max.setValue(10)
        self.max.setObjectName("max")
        self.horizontalLayout.addWidget(self.max)
        QMetaObject.connectSlotsByName(self)
        
    def setParams(self, name, min_value, max_value, suffix, minimum=-99, maximum=99):
        self.label.setText(name)
        self.min.setMinimum(minimum)
        self.max.setMaximum(maximum)
        self.min.setValue(min_value)
        self.max.setValue(max_value)
        self.min.setSuffix(suffix)
        self.max.setSuffix(suffix)
        
    def value(self):
        return (self.min.value(), self.max.value())
        

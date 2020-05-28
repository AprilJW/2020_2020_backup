from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import pyqtSlot

import sys
from PyQt5.QtWidgets import QApplication

from ui.MainWindow import QWidget

class SliderAndSpinBoxWidget(QWidget):

    valueChanged = pyqtSignal(int)
    
    def __init__(self, parent):
        super(QWidget, self).__init__()
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.horizontalSlider = QSlider(self)
        self.horizontalSlider.setOrientation(Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.horizontalLayout.addWidget(self.horizontalSlider)
        self.spinBox = QSpinBox(self)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout.addWidget(self.spinBox)
        self.label_note = QLabel(self)
        self.label_note.setObjectName("note")
        self.horizontalLayout.addWidget(self.label_note)
        QMetaObject.connectSlotsByName(self)
        
    def setName(self, name):
        self.label.setText(name)
        
    def setMinMax(self, min_value, max_value):
        self.horizontalSlider.setMinimum(min_value)
        self.horizontalSlider.setMaximum(max_value)
        self.spinBox.setMinimum(min_value)
        self.spinBox.setMaximum(max_value)
        
    def setDefaultValue(self, value):
        self.horizontalSlider.setValue(value)
        self.spinBox.setValue(value)
        
    def setSuffix(self, suffix):
        self.spinBox.setSuffix(suffix)
        
    def setPrefix(self, prefix):
        self.spinBox.setPrefix(prefix)
    
    def setNote(self, text):
        self.label_note.setText(text)
        
    @pyqtSlot(int)
    def on_horizontalSlider_valueChanged(self, value):
        self.spinBox.setValue(value)
        self.valueChanged.emit(value)
    @pyqtSlot(int)
    def on_spinBox_valueChanged(self, value):
        self.horizontalSlider.setValue(value)
        self.valueChanged.emit(value)
        
    def value(self):
        return self.spinBox.value()
    
    def set_note_width(self, width):
        self.label_note.setMinimumWidth(width)
        
    def set_spinBox_width(self, width):
        self.spinBox.setMinimumWidth(width)
    
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = SliderAndSpinBoxWidget(0)
    mainwindow.setMinMax(0, 30000)
    
    mainwindow.set_spinBox_width(60)
    mainwindow.setNote('/12345',45)
    mainwindow.show()
    sys.exit(app.exec_())

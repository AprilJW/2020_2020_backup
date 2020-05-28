from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.Qt import pyqtSlot,pyqtSignal

class ROIWidget(QtWidgets.QWidget):
    roi_changed = pyqtSignal(int, int, int, int)#x,y,w,h
    def __init__(self, parent):
        super(QtWidgets.QWidget, self).__init__()
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.x = QtWidgets.QSpinBox(self)
        self.x.setMaximum(9999)
        self.x.setObjectName("x")
        self.horizontalLayout.addWidget(self.x)

        self.y = QtWidgets.QSpinBox(self)
        self.y.setMaximum(9999)
        self.y.setObjectName("y")
        self.horizontalLayout.addWidget(self.y)
 
        self.w = QtWidgets.QSpinBox(self)
        self.w.setMaximum(9999)
        self.w.setObjectName("w")
        self.horizontalLayout.addWidget(self.w)

        self.h = QtWidgets.QSpinBox(self)
        self.h.setMaximum(9999)
        self.h.setObjectName("h")
        self.horizontalLayout.addWidget(self.h)
        QtCore.QMetaObject.connectSlotsByName(self)
        
    @pyqtSlot(int)
    def on_x_valueChanged(self, value):
        self.roi_changed.emit(*self.value())
        
    @pyqtSlot(int)
    def on_y_valueChanged(self, value):
        self.roi_changed.emit(*self.value())
        
    @pyqtSlot(int)
    def on_w_valueChanged(self, value):
        self.roi_changed.emit(*self.value())
        
    @pyqtSlot(int)
    def on_h_valueChanged(self, value):
        self.roi_changed.emit(*self.value())
              
    def setValue(self, x, y, w, h):
        self.x.setValue(x)
        self.y.setValue(y)
        self.w.setValue(w)
        self.h.setValue(h)
    
    def value(self):
        return (self.x.value(), self.y.value(), self.w.value(), self.h.value())
    
    def roi_width(self):
        return self.w.value()
    
    def roi_height(self):
        return self.h.value()



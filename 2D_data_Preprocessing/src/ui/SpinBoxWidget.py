from PyQt5.Qt import QEvent, QWidget, QSpinBox, QDoubleSpinBox
from PyQt5 import QtCore

class SpinBoxWidget(QSpinBox):
    def __init__(self, parent=None):
        QSpinBox.__init__(self, parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and isinstance(obj, __class__) and not obj.hasFocus():
            event.ignore()
            return True
        return QWidget.eventFilter(self, obj, event)

    def setEnable(self, bool):
        super().setEnabled(bool)


class DoubleSpinBoxWidget(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setDecimals(3)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and isinstance(obj, __class__) and not obj.hasFocus():
            event.ignore()
            return True
        return QWidget.eventFilter(self, obj, event)

    def setEnable(self, bool):
        super().setEnabled(bool)
        
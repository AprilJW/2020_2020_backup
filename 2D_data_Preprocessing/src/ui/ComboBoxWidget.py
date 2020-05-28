from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class ComboBox(QWidget):
    valChanged = pyqtSignal()

    def __init__(self, parent):
        super().__init__()

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._combo_box = QComboBox()
        self._combo_box.currentIndexChanged.connect(self.on_val_change)
        self._layout.addWidget(self._combo_box)
        self.setLayout(self._layout)

    @pyqtSlot()
    def on_val_change(self):
        self.selected_opt = self._combo_box.currentText()
        self.valChanged.emit()

    def add_opts(self, enum_opts=[]):
        self._combo_box.addItems(enum_opts)

    def current_opt(self):
        return self.selected_opt
    
    def setCurrentText(self, current_text):
        self._combo_box.setCurrentText(current_text)


if __name__ == '__main__':
    import sys
    from PyQt5.QtGui import *

    app = QApplication(sys.argv)
    ex = ComboBox(parent=None)
    ex.add_opts(['Java', 'C#', 'Python'])
    ex.show()
    sys.exit(app.exec_())

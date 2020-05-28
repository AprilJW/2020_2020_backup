from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class BrowsePath(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.path = QLineEdit(self)
        self.path.setObjectName("filePath")
        self.horizontalLayout.addWidget(self.path)
        self.browse = QPushButton(self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.browse.sizePolicy().hasHeightForWidth())
        self.browse.setSizePolicy(sizePolicy)
        self.browse.setMinimumSize(QSize(20, 0))
        self.browse.setMaximumSize(QSize(20, 16777215))
        self.browse.setObjectName("browse")
        self.horizontalLayout.addWidget(self.browse)
        self.path.textChanged.connect(self.on_val_changed)
        QMetaObject.connectSlotsByName(self)

    @pyqtSlot(str)
    def on_val_changed(self, path):
        self.valChanged.emit(path)
        pass

    @pyqtSlot()
    def on_browse_clicked(self):
        pass

    def set_path(self, path):
        self.path.setText(path)

    def value(self):
        return self.path.text()

    def empty(self):
        return len(self.path.text()) == 0


class BrowseDirPath(BrowsePath):
    valChanged = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)

    @pyqtSlot()
    def on_browse_clicked(self):
        _dirPath = QFileDialog.getExistingDirectory(self, 'Open Directory', ".",
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)
        self.set_path(path=_dirPath)


class BrowseFilePath(BrowsePath):
    valChanged = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)

    @pyqtSlot()
    def on_browse_clicked(self):
        _filePath, _ = QFileDialog.getOpenFileName(self, 'Open File', '.', 'All Files (*)')
        self.set_path(path=_filePath)


if __name__ == "__main__":
    import sys
    from PyQt5.QtGui import *

    app = QApplication(sys.argv)
    myshow = BrowseFilePath(parent=None)
    myshow.show()
    sys.exit(app.exec_())

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class BrowseFilePath(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__()
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.filePath = QLineEdit(self)
        self.filePath.setObjectName("filePath")
        self.horizontalLayout.addWidget(self.filePath)
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
        QMetaObject.connectSlotsByName(self)
        
    def setName(self, name):
        self.label.setText(name)
        
    @pyqtSlot()
    def on_browse_clicked(self):
        self.dirPath = QFileDialog.getExistingDirectory(self, 'Open Directory', ".",
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)
        self.filePath.setText(self.dirPath)
    
    def setPath(self, dir_path):
        self.filePath.setText(dir_path)
        
    def value(self):
        return self.filePath.text()
    
    def empty(self):
        return len(self.filePath.text()) == 0


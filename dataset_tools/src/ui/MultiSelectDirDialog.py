from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import QFileDialog, QMessageBox
import os
import platform

class FileDialog(QFileDialog):
    def __init__(self, *args):
        QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.selectedFiles = []
        self.tree = self.findChild(QTreeView)

    def openClicked(self):
        inds = self.selectedParents()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()),str(i.data())))
        self.selectedFiles = files
        self.hide()
    
    def filesSelected(self):
        return self.selectedFiles

    def selectedParents(self):
        indexes=self.tree.selectionModel().selectedIndexes()
        for index in indexes:
            while index.parent().isValid():
                index = index.parent()
        return indexes

class MultiSelectDirDialog(QFrame): 
    def __init__(self, parent):
        super(QFrame, self).__init__()
        self.verticalLayout_2 = QVBoxLayout(self)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.widget_3 = QWidget(self)
        self.widget_3.setObjectName("widget_3")
        self.horizontalLayout = QHBoxLayout(self.widget_3)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget_2 = QWidget(self.widget_3)
        self.widget_2.setObjectName("widget_2")
        self.verticalLayout = QVBoxLayout(self.widget_2)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.format_add_dir = QPushButton(self.widget_2)
        self.format_add_dir.setObjectName("format_add_dir")
        self.format_add_dir.setText("+")
        self.verticalLayout.addWidget(self.format_add_dir)
        self.format_remove_dir = QPushButton(self.widget_2)
        self.format_remove_dir.setObjectName("format_remove_dir")
        self.format_remove_dir.setText("-")
        self.verticalLayout.addWidget(self.format_remove_dir)
        self.format_clear_dir = QPushButton(self.widget_2)
        self.format_clear_dir.setObjectName("format_clear_dir")
        self.format_clear_dir.setText("clear")
        self.verticalLayout.addWidget(self.format_clear_dir)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout.addWidget(self.widget_2)
        self.dirList = QListWidget(self.widget_3)
        self.dirList.setObjectName("dirList")
        self.dirList.setDragDropMode(QAbstractItemView.InternalMove)
        self.horizontalLayout.addWidget(self.dirList)
        self.verticalLayout_2.addWidget(self.widget_3)

        QMetaObject.connectSlotsByName(self)
        plat_form = platform.system()
        if plat_form == 'Linux':
            self.lastOpenDir = os.path.expanduser("~/Data")
        elif plat_form == 'Windows':
            self.lastOpenDir = os.path.expanduser("D:/Data")

    @pyqtSlot()
    def on_format_add_dir_clicked(self):
        dir_paths = self._open_dirs()
        for dir_path in dir_paths:
            if len(dir_path) != '':
                self.add_one_dir(dir_path)

    @pyqtSlot()
    def on_format_remove_dir_clicked(self):
        for selectedItem in self.dirList.selectedItems():
            self.dirList.takeItem(self.dirList.row(selectedItem))
            
    @pyqtSlot()
    def on_format_clear_dir_clicked(self):
        self.dirList.clear()

    @pyqtSlot()
    def on_mergeDir_clicked(self):
        if self.dirList.count() < 1:
            QMessageBox.information(self, "Info", "dir list is empty")
            return
        dest_dir = self._open_dir()
        if len(dest_dir) == 0:
            return
        self._mergeDirs(dest_dir)
        QMessageBox.information(self, "info", "merge dir for " + str(self.dirList.count()) + " finished")

    @pyqtSlot(QListWidgetItem)
    def on_dirList_itemActivated(self, item):
        self.dirList.setCurrentItem(item)
    
    def add_one_dir(self, dir_path): 
        item = QListWidgetItem(dir_path)
        self.dirList.addItem(item)
        self.dirList.setCurrentItem(item)
        
    def selected_dirs(self):
        dirs = []
        for i in range(self.dirList.count()):
            dirs.append(self.dirList.item(i).text())
            
        return dirs

    def empty(self):
        return self.dirList.count() == 0
            
    def _open_dirs(self):
        file_name = FileDialog()
        file_name.setViewMode(QFileDialog.Detail)
        file_name.exec_()
        return file_name.filesSelected()

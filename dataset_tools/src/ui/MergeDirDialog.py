from PyQt5.QtWidgets import QFrame, QVBoxLayout, QPushButton, QMessageBox, QFileDialog
from PyQt5.QtCore import QMetaObject, pyqtSlot
from ui.MultiSelectDirDialog import MultiSelectDirDialog

from libs import voc_data_checker
from libs.dir_and_filename_info import *
from libs import xml_to_json
import os
import logging
    
class MergeDirDialog(QFrame):
    def __init__(self, parent):
        super(QFrame, self).__init__()
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout_2")

        self.multi_select_dir_dialog = MultiSelectDirDialog(self)
        self.verticalLayout.addWidget(self.multi_select_dir_dialog)
        self.mergeDir = QPushButton(self)
        self.mergeDir.setObjectName("mergeDir")
        self.mergeDir.setText("Merge Selected Dirs To One Dir")
        self.verticalLayout.addWidget(self.mergeDir)

        QMetaObject.connectSlotsByName(self)
        self.lastOpenDir = "."
        
    @pyqtSlot()
    def on_mergeDir_clicked(self):
        if self.multi_select_dir_dialog.empty():
            QMessageBox.information(self, "Info", "dir list is empty")
            return
        dest_dir = self._open_dir()

        num_depth_dirs = 0
        for src_dir in self.multi_select_dir_dialog.selected_dirs():
            if os.path.exists(os.path.join(src_dir,'depth_images')):
                num_depth_dirs += 1
     
        if (num_depth_dirs > 0) and (num_depth_dirs < (len(self.multi_select_dir_dialog.selected_dirs()))):
            QMessageBox.critical(self, "Error",
                                    "Some of the given folders have depth images, some not. Please delete or complete all the depth images.")
            exit(0)

        if len(dest_dir) == 0:
            return
        self._mergeDirs(dest_dir)
        QMessageBox.information(self, "info", "merge dir for " + str(len(self.multi_select_dir_dialog.selected_dirs())) + " finished")
        
    def _mergeDirs(self, destDir):
        dest_images_dir = get_dir_path(destDir, DIR_IMAGES, create_if_not_exist=True)
        dest_depth_dir = get_dir_path(destDir, DIR_DEPTH, create_if_not_exist=True)
        dest_labels_dir = get_dir_path(destDir, DIR_LABELS, create_if_not_exist=True)
        last_img_index = 0

        for src_dir in self.multi_select_dir_dialog.selected_dirs():
            if not is_images_path_exist(src_dir) or not is_labels_path_exist(src_dir):
                split_dir_to_images_labels(src_dir)
            last_img_index = voc_data_checker.rename_jpg_files(src_dir, "2007_", last_img_index, zero_fill = 6)
            logging.debug("last index after rename: " + str(last_img_index))
            src_images_dir = os.path.join(src_dir, DIR_IMAGES)
            src_depth_dir = os.path.join(src_dir, DIR_DEPTH)
            src_labels_dir = os.path.join(src_dir, DIR_LABELS)
            merge_two_dirs(src_images_dir, dest_images_dir)
            merge_two_dirs(src_depth_dir, dest_depth_dir)
            merge_two_dirs(src_labels_dir, dest_labels_dir)
        xml_to_json.xmltojson_dir(destDir)
            
        
    def _open_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Open Directory', self.lastOpenDir,
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)

        self.lastOpenDir = dir_path
        return dir_path

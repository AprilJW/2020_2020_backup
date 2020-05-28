import os
from PyQt5.Qt import QDialog
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMessageBox
import platform
import logging

from ui.Ui_DepthEncodingDialog import Ui_DepthEncodingDialog as ui
from libs.depth_encoding.depth_encoding import start_depth_encoding
from libs.dataset_format.DatasetFormatter import DatasetFormatter
from libs.dir_and_filename_info import *
from Image_comparer.Comparer import Comparer


class DepthEncodingDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.ui = ui()
        self.ui.setupUi(self)

        if platform.system() == 'Windows':
            self.last_open_dir_path = os.getenv('userprofile')
        else:
            self.last_open_dir_path = '~/'

    @pyqtSlot()
    def on_start_depth_encoding_clicked(self):
        logging.info("Starting depth encoding")
        depth_src_type = self.ui.depth_source_type.currentIndex()
        depth_encode_type = self.ui.depth_encoding_type.currentIndex()
        depth_src_path = self.src_dir
        depth_dest_path = self.src_dir
        rgb_image_path = self.src_dir
        # convert depth file to images
        if is_images_labels_depth_mixed(self.src_dir):
            split_dir_to_images_labels(self.src_dir)
        if is_images_path_exist(self.src_dir):
            depth_src_path = os.path.join(self.src_dir, DIR_DEPTH)
            depth_dest_path = os.path.join(self.src_dir, DIR_DEPTH_ENCODED)
            rgb_image_path = os.path.join(self.src_dir, DIR_IMAGES)
        elif os.path.basename(self.src_dir) in [DIR_IMAGES, DIR_DEPTH]:
            depth_src_path = os.path.join(os.path.dirname(self.src_dir), DIR_DEPTH)
            depth_dest_path = os.path.join(os.path.dirname(self.src_dir), DIR_DEPTH_ENCODED)
            rgb_image_path = os.path.join(os.path.dirname(self.src_dir), DIR_IMAGES)
        else:
            QMessageBox.warning(self, "warning", "image dir error!")
            return

        if not os.path.exists(depth_src_path) or len(os.listdir(depth_src_path)) == 0:
            QMessageBox.warning(self, "warning",  "depth dir not exist or empty!")
            return
        min_val = self.ui.depth_encoding_min.value()
        max_val = self.ui.depth_encoding_max.value()
        self.encoding = start_depth_encoding(depth_src_path, depth_dest_path, depth_src_type, depth_encode_type,
                                             [min_val, max_val])
        logging.info("done")
        QMessageBox.information(self, "Info", 'Success')
        image_dirs = []
        image_dirs.append(rgb_image_path)
        image_dirs.append(depth_dest_path)
        self.rgb_depth_comparer = Comparer(len(image_dirs))
        for image_path in image_dirs:
            self.rgb_depth_comparer.multi_select_dialog.add_one_dir(image_path)


    def set_src_dir(self, src_dir, img_num):
        self.src_dir = src_dir
        self.img_num = img_num
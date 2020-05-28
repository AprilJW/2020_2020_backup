import os
from PyQt5.Qt import QDialog
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog

from ui.Ui_DataSetFormatDialog import Ui_DataSetFormatDialog as ui
from libs.dataset_format import dataset_formatter_factory
from libs.dir_and_filename_info import *
from libs.shuffle_and_rename import *
from libs.check_dataset_valid import *
from libs import voc_data_checker, xml_to_json
from libs.dataset_format.dataset_utilities.dataset_util import DATASET_TYPES
from libs.dataset_format.DatasetFormatter import DatasetFormatter
from libs.dataset_format.dataset_utilities.json_util import JsonUtil

import platform
from numpy import log10 as log10
from numpy import floor as floor

class DataSetFormatDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.ui = ui()
        self.ui.setupUi(self)
        self.ui.widget_outpath.setName("Output DataSet Path")
        self.ui.slider_train.setName('train/total')
        self.ui.slider_minival.setName('minival/val')

        if platform.system() == 'Windows':
            self.lastOpenDir = os.getenv('userprofile')
        else:
            self.lastOpenDir = '~/'

        self.ui.slider_train.set_note_width(45)
        self.ui.slider_minival.set_note_width(45)
        self.ui.slider_train.set_spinBox_width(60)
        self.ui.slider_minival.set_spinBox_width(60)
        self.ui.slider_train.valueChanged.connect(self.on_slider_train_valueChanged)

        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../libs/dataset_format/coco_format',
                                   'config.json')
        data_json = JsonUtil.from_file(self.config_path)
        data = data_json.__dict__
        self.ui.image_size_h.setText(str(data['image_size']['height']))
        self.ui.image_size_w.setText(str(data['image_size']['width']))


    @pyqtSlot(int)
    def on_slider_train_valueChanged(self, train_num):
        val_num = self.img_num - train_num
        self.ui.slider_minival.setMinMax(0, val_num)
        self.ui.slider_minival.setNote('/'+str(val_num))
        
    @pyqtSlot()
    def on_browse_output_path_clicked(self):
        self.ui.output_path.setText(self._open_dir())

    @pyqtSlot()
    def on_start_format_dataset_clicked(self):
        logging.info("Starting format dataset")
        if self.ui.widget_outpath.empty():
            QMessageBox.warning(self, "warning", "please set output path")
            return

        formatter_types = self._read_formatter_types()
        try:
            for dataset_type in formatter_types:
                formatter = dataset_formatter_factory.construct_formatter(dataset_type)
                self._set_formatter_config(formatter)
                formatter.start_format()
            QMessageBox.information(self, "Info", 'Success')
        except Exception as e:
            QMessageBox.warning(self, "Exception", str(e))
            
    @pyqtSlot(int)
    def on_hSlider_train_sliderMoved(self,value):
        self.ui.spinBox_train.setValue(self.ui.hSlider_train.value())
        
    def set_src_dir(self, src_dir, img_num):
        self.src_dir = src_dir
        self.img_num = img_num
        self.lastOpenDir = src_dir
        logging.info("Starting auto set train params")
        self.auto_set_train_params()

    def auto_set_train_params(self):
        validation_dir = os.path.join(self.src_dir, DIR_VALIDATION)
        if os.path.isdir(validation_dir):
            logging.info("train num:{0}".format(self.img_num))
            train_num = self.img_num 
            voc_data_checker.rename_jpg_files(validation_dir, "2007_", train_num, zero_fill = 6)
            logging.info("Moving validation files ......")
            if not is_images_path_exist(validation_dir) or not is_labels_path_exist(validation_dir):
                split_dir_to_images_labels(validation_dir)
            if not check_if_json_labeled(validation_dir):
                xml_to_json.xmltojson_dir(validation_dir)
                
            val_num = len(os.listdir(os.path.join(validation_dir, DIR_IMAGES)))
            move_files(os.path.join(validation_dir, DIR_IMAGES), os.path.join(self.src_dir, DIR_IMAGES))
            move_files(os.path.join(validation_dir, DIR_LABELS), os.path.join(self.src_dir, DIR_LABELS))
            shutil.rmtree(validation_dir)
            logging.info("validation num:{0}".format(val_num))
            minival_num = val_num -1 
            self.img_num = train_num + val_num
            self.ui.slider_train.setEnabled(False)  
            self.ui.slider_minival.setEnabled(False)         
        else:
            if self.img_num < 2000:
                train_num = round(0.9*self.img_num)
                val_num = self.img_num - train_num
                minival_num = val_num-1
            else:
                train_num = self.img_num - 200
                val_num = 200
                minival_num = val_num - 1
            total = self.img_num
            
            self.ui.slider_train.setEnabled(True)  
            self.ui.slider_minival.setEnabled(True)
        print("@@@",self.img_num, train_num, val_num, minival_num)  
        self.set_ui_train_val_minival(self.img_num, train_num, val_num, minival_num)
                
    def set_ui_train_val_minival(self,total, train, val, minival):
        self.ui.slider_train.setMinMax(0,total)
        self.ui.slider_minival.setMinMax(0,val)
            
        self.ui.slider_train.setNote('/'+str(total))
        self.ui.slider_minival.setNote('/'+str(val))
            
        self.ui.slider_train.setDefaultValue(train)
        self.ui.slider_minival.setDefaultValue(minival)

    def _read_formatter_types(self):
        formatter_types = []
        if self.ui.generate_voc.isChecked():
            formatter_types.append(DATASET_TYPES.VOC.name)
        if self.ui.generate_coco.isChecked():
            formatter_types.append(DATASET_TYPES.COCO.name)
        if self.ui.generate_cityscapes.isChecked():
            formatter_types.append(DATASET_TYPES.CS.name)
        return formatter_types

    def _set_formatter_config(self, dataset_formatter=DatasetFormatter()):
        dataset_formatter.debug_status = self.ui.debug_mode.isChecked()
        dataset_formatter.paths[DIR_IMAGES] = os.path.join(self.src_dir, DIR_IMAGES)
        dataset_formatter.paths[DIR_DEPTH] = os.path.join(self.src_dir, DIR_DEPTH)
        dataset_formatter.paths[DIR_LABELS] = os.path.join(self.src_dir, DIR_LABELS)
        dataset_formatter.paths['output'] = self.ui.widget_outpath.value()
        dataset_formatter.unify_categories = self.ui.unify_categories.isChecked()
        dataset_formatter.split_ids['train'] = self.ui.slider_train.value() - 1
        dataset_formatter.split_ids['minival'] = self.ui.slider_train.value() + self.ui.slider_minival.value() - 1
        dataset_formatter.split_ids['val'] = self.img_num-1
        dataset_formatter.background_color = [self.ui.color_b.value(), self.ui.color_g.value(), self.ui.color_r.value()]
        dataset_formatter.separation_linewidth = self.ui.mask_separation_linewidth.value()
        dataset_formatter.generate_hierarchy_json = self.ui.cityscapes_hierarchy_format.isChecked()

        return dataset_formatter

    def _open_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Open Directory', self.lastOpenDir,
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)

        self.lastOpenDir = dir_path
        return dir_path
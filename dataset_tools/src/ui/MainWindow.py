from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import pyqtSlot

import PyQt5
import os
import cv2
import copy
import logging
from tqdm import tqdm
import platform
from canvas import Canvas
from ui import FormatVocDataWidget as voc_widget
from ui import Ui_MainWindow as ui
from ui import DataSetFormatDialog as dataset_dialog
from ui import OptionDialog as option

from libs import voc_data_checker, check_dataset_valid
from libs import image_utils
from libs.label_util import *
from libs.check_dataset_valid import *
from libs import xml_to_json
from libs import json_to_xml
from libs import settings
from libs import data_operations
from libs.shuffle_and_rename import shuffle_and_rename_local
from libs.coco_parser.coco_parser import CocoParser
from libs.image_statistics import compute_and_save_rgb_mean

import re

__appname__ = "Dataset Tools"
    
def notify_operation_finished(operation, file_num):
    QMessageBox.information(None, 'info', operation + ' success for ' + str(file_num) + " files finished")
    
def notify_operation_error(operation, msg):
    QMessageBox.warning(None, 'warning', operation + " failed: " + msg)
       
    
COLORS = {
    'NOTSET': Qt.darkGreen,
    'DEBUG': Qt.darkBlue,
    'INFO': Qt.black,
    'WARNING': Qt.magenta,
    'CRITICAL': Qt.red,
    'ERROR': Qt.red
}
    
class LoggingHandler(QObject, logging.Handler):
    newLogging = pyqtSignal(QColor, str)

    def __init__(self, level=logging.NOTSET):
        QObject.__init__(self)
        logging.Handler.__init__(self, level=level)
        try:
            self.setFormatter(logging.root.handlers[0].formatter)
        except IndexError:
            pass

    def emit(self, record):
        msg = self.format(record)
        color = Qt.black
        if record.levelname in COLORS:
            color = COLORS[record.levelname]
        self.newLogging.emit(color, msg)
      
class MainWindow(QMainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.on_loggingLevel_currentIndexChanged(self.ui.loggingLevel.currentIndex())
        self.canvas = Canvas(self.ui.scrollArea)
        self.canvas.scrollRequest.connect(self.scrollRequest)
        
        self.ui.fileList.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        self.ui.fileList.currentRowChanged.connect(self.fileitemClicked)
        self.ui.scrollArea.setWidget(self.canvas)
        self.ui.scrollArea.setWidgetResizable(True)
        
        self.canvas.rgbValueGot.connect(self.on_rgbValueReceived)
        self.canvas.roiSelected.connect(self.on_roi_received)
        self.ui.roi_widget.roi_changed.connect(self.on_roi_changed)

        self.ui.widget_brightness.setParams("brightness", -20, 20, '')
        self.ui.widget_contrast.setParams("contrast", -10, 10, '%')
        self.ui.widget_scale.setParams("scale", -15, 15, '%')
        self.ui.widget_rotation.setParams("rotation", -180, 180, '', -180, 180)
        self.ui.widget_translation.setParams("translation", -300, 300, '', -500, 500)
        
        self.initDockWidgets()
        self.format_voc_widget = voc_widget.FormatVocDataWidget()
        self.dataset_format_widget = dataset_dialog.DataSetFormatDialog()
        self.ui.dataset_type.setStyleSheet("QLabel {color : red; }")
        # self.depth_encoding_widget = depth_dialog.DepthEncodingDialog()

        self.LoggintHandler = LoggingHandler()
        logging.getLogger().addHandler(self.LoggintHandler)
        self.LoggintHandler.newLogging.connect(self.outputLogging)
        self.ui.logger.setReadOnly(True)
        
        self.ui.clear_log.clicked.connect(self.ui.logger.clear)
        
        self.scrollBars = {
            Qt.Vertical: self.ui.scrollArea.verticalScrollBar(),
            Qt.Horizontal: self.ui.scrollArea.horizontalScrollBar()
        }

        settings.load_settings("setting.ini", self.ui)
        self.updateDockWidgets()
        self.canvas.enable_drawing_roi = (self.ui.resize_mode.currentText() == RESIZE_MODE_ROI)
        self.on_resize_mode_currentTextChanged(self.ui.resize_mode.currentText())
        
        self.mImgList = []
        self.dirname = None
        if platform.system() == 'Windows':
            self.lastOpenDir = os.getenv('userprofile')
        else:
            self.lastOpenDir = '~/'
        self.fileListIndex = -1
        self.is_cocodataset = False
        self.is_vocdataset = False

    @pyqtSlot(QColor, str)
    def outputLogging(self, color, msg):
        tf = self.ui.logger.currentCharFormat()
        tf.setForeground(QBrush(color))
        self.ui.logger.setCurrentCharFormat(tf)
        self.ui.logger.appendPlainText(msg)
        
    @pyqtSlot(int)
    def on_loggingLevel_currentIndexChanged(self, index):
        logging.getLogger().setLevel(index * 10)

    @pyqtSlot()
    def on_actionOpen_triggered(self):
        self.openFile()
            
    @pyqtSlot()
    def on_actionOpen_Dir_triggered(self):
        self.openDir()
        
    @pyqtSlot()
    def on_actionNext_Image_triggered(self):
        self.openNextImg()
    
    @pyqtSlot()
    def on_actionPrev_Image_triggered(self):
        self.openPrevImg()

    @pyqtSlot(bool)   
    def on_actionShow_File_List_triggered(self, checked):
        self.ui.dock_file_list.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionResize_Params_triggered(self, checked):
        self.ui.dock_resize_files.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionChange_Pixel_Values_triggered(self, checked):
        self.ui.dock_change_pixel_values.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionAugment_Data_triggered(self, checked):
        self.ui.dock_augment_data.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionRename_Files_triggered(self, checked):
        self.ui.dock_rename_files.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionImage_Preview_triggered(self, checked):
        self.ui.dock_image_preview.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionShow_Log_triggered(self, checked):
        self.ui.dock_logger.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionMerge_Dir_triggered(self, checked):
        self.ui.dock_merge_dir.setVisible(checked)
        
    @pyqtSlot(bool)   
    def on_actionVoc_Data_Format_triggered(self, checked):
        self.format_voc_widget.setSrcPath(self.dirname)
        self.format_voc_widget.show()
        
    @pyqtSlot()
    def on_actionShuffle_triggered(self):
        if not self.confirm_operation("shuffle and rename locally"):
            return
        shuffle_and_rename_local(self.dirname)
        notify_operation_finished("shuffle and rename locally ", len(self.mImgList))   
    
    @pyqtSlot(str)
    def on_resize_mode_currentTextChanged(self,resize_mode):
        self.ui.widget_rgb_resize.setVisible(resize_mode == RESIZE_MODE_FILL)
        
        resize_need_width_height = [RESIZE_MODE_CROP, RESIZE_MODE_FILL, RESIZE_MODE_ROI]
        self.ui.label_width.setVisible(resize_mode in resize_need_width_height)
        self.ui.new_img_width.setVisible(resize_mode in resize_need_width_height)
        self.ui.label_height.setVisible(resize_mode in resize_need_width_height)
        self.ui.new_img_height.setVisible(resize_mode in resize_need_width_height)
        
        self.ui.label_scale.setVisible(resize_mode == RESIZE_MODE_PLAIN or resize_mode == RESIZE_MODE_ROI)
        self.ui.img_scale_ratio.setVisible(resize_mode == RESIZE_MODE_PLAIN or resize_mode == RESIZE_MODE_ROI)
        self.ui.roi_widget.setVisible(resize_mode == RESIZE_MODE_ROI)
        self.ui.label_resize_roi.setVisible(resize_mode == RESIZE_MODE_ROI)
        self.ui.resize_file.setVisible(resize_mode == RESIZE_MODE_FILE)
        self.ui.label_resize_file.setVisible(resize_mode == RESIZE_MODE_FILE)
        self.canvas.enable_drawing_roi = (resize_mode == RESIZE_MODE_ROI)
        
    @pyqtSlot()   
    def on_actionWrite_File_List_triggered(self):
        if not self.verify_dir_path():
            return

        write_file_list(self.dirname, self.mImgList)
        notify_operation_finished("write file list to current dir", len(self.mImgList))
    
    @pyqtSlot()   
    def on_actionMerge_Images_Labels_triggered(self):
        if not self.verify_dir_path():
            return
        merge_images_labels_to_one_dir(self.dirname)
        self.reloadImg(self.dirname)

    @pyqtSlot()
    def on_actionSplit_Dir_triggered(self):
        if not self.verify_dir_path():
            return
        split_dir_to_images_labels(self.dirname)
        self.reloadImg(self.dirname)

    @pyqtSlot()
    def on_actionXml_To_Json_triggered(self):
        if not self.confirm_operation("xml to json"):
            return
        xml_to_json.xmltojson_dir(self.dirname)     
        notify_operation_finished("convert mask xml to json", len(self.mImgList))
        self.reloadImg(self.dirname)
    
    @pyqtSlot()
    def on_actionJson_To_Xml_triggered(self):
        if not self.confirm_operation("json to xml"):
            return
        dialog = option.OptionDialog(self, "json to xml", [XML_TYPE_VERTEX, XML_TYPE_BNDBOX, XML_TYPE_MIX])
        if QDialog.Rejected == dialog.exec():
            return
        xml_type = dialog.current_option()
        logging.info("xml: {0}".format(xml_type))
        json_to_xml.jsontoxml_dir(self.dirname, xml_type)
        notify_operation_finished("convert json to xml for detection ", len(self.mImgList))
        self.reloadImg(self.dirname)
    
    @pyqtSlot()
    def on_actionStart_Format_DataSet_triggered(self):
        if not self.verify_dir_path():
            return
        if not check_if_images_labels(self.dirname):
            notify_operation_error("format dataset", "please format dir to images and labels first")
            return
        if not check_if_file_name_valid(self.dirname):
            notify_operation_error("format dataset", "please rename images and labels first")
            return
        if not check_if_json_labeled(self.dirname):
            notify_operation_error("format dataset", "please convert xml to json first")
            return
        check_dataset_valid.check_rgb_depth_size_match(self.dirname)
        
        logging.info("Starting shuffle and rename images")
        if QMessageBox.Yes == QMessageBox.question(self, "info", "Starting shuffle and rename images", QMessageBox.Yes | QMessageBox.Cancel):
            shuffle_and_rename_local(self.dirname)
            
        self.dataset_format_widget.set_src_dir(self.dirname, len(self.mImgList))
        self.dataset_format_widget.show()

    @pyqtSlot()
    def on_actionDepth_Encoding_triggered(self):
        from ui import DepthEncodingDialog as depth_dialog
        self.depth_encoding_widget = depth_dialog.DepthEncodingDialog()
        if not self.verify_dir_path():
            return
        self.depth_encoding_widget.set_src_dir(self.dirname, len(self.mImgList))
        self.depth_encoding_widget.show()

    @pyqtSlot()
    def on_actionCompute_rgb_mean_triggered(self):
        if not self.verify_dir_path():
            return
        compute_and_save_rgb_mean(self.dirname, os.path.dirname(self.dirname))
        print('compute rgb mean done')

    @pyqtSlot()
    def on_actionSave_mask_triggered(self):
        for i in os.listdir(os.path.join(self.dirname, "images")):
            img = QImage(os.path.join(self.dirname, "images", i))
            exist, label_full_path = is_label_file_exist(self.dirname, os.path.join(self.dirname, "images", i))
            label_type, vertex_infos = read_label_file(label_full_path)
            painter = QPainter(img)
            self.canvas.draw_label_infos(painter, vertex_infos)
            painter.end()
            if not os.path.exists(os.path.join(self.dirname, "images_with_mask")):
                os.makedirs(os.path.join(self.dirname, "images_with_mask"))
            img.save(os.path.join(self.dirname, "images_with_mask", i))

    @pyqtSlot()
    def on_actionBmp_To_Jpg_triggered(self):
        if not self.confirm_operation("convert all bmp to jpg"):
            return
        for file in tqdm(self.mImgList, "bmp to jpg:"):
            if os.path.splitext(file)[1] == '.bmp':
                img = cv2.imread(file)
                new_img_path = os.path.splitext(file)[0] + '.jpg'
                cv2.imwrite(new_img_path, img)
                os.remove(file) 
        notify_operation_finished("convert bmp to jpg ", len(self.mImgList))
        self.reloadImg(self.dirname)              
            
    @pyqtSlot(int)   
    def on_pixelValue_valueChanged(self, value):
        self.canvas.setPixelValueHighlight(value)
    
    def initDockWidgets(self):
        self.ui.dock_file_list.setVisible(True)
        self.ui.dock_resize_files.setVisible(False)
        self.ui.dock_change_pixel_values.setVisible(False)
        self.ui.dock_augment_data.setVisible(False)
        self.ui.dock_rename_files.setVisible(False)
        self.ui.dock_logger.setVisible(True)
        self.ui.old_value_text.setEnabled(False)
        self.ui.modify_none_zero.setChecked(True)

    def updateDockWidgets(self):
        self.ui.dock_file_list.setVisible(self.ui.actionShow_File_List.isChecked())
        self.ui.dock_resize_files.setVisible(self.ui.actionRename_Files.isChecked())
        self.ui.dock_change_pixel_values.setVisible(self.ui.actionChange_Pixel_Values.isChecked())
        self.ui.dock_augment_data.setVisible(self.ui.actionAugment_Data.isChecked())
        self.ui.dock_rename_files.setVisible(self.ui.actionRename_Files.isChecked())
        self.ui.dock_logger.setVisible(self.ui.actionShow_Log.isChecked())
        self.ui.old_value_text.setEnabled(not self.ui.modify_none_zero.isChecked())
        
    @pyqtSlot()   
    def on_modifyPixelValues_clicked(self):
        text = self.ui.old_value_text.text()
        old_value_split = text.split(',') 
        old_values = [int(i) for i in old_value_split]
        
        for file in tqdm(self.mImgList, "change pixel values:"):
            image_utils.changePixelsValue(file, old_values, self.ui.newPixelValue.value(), self.ui.modify_none_zero.isChecked())

        notify_operation_finished("change pixel values ", len(self.mImgList))
        self.reloadImg(self.dirname) 

    @pyqtSlot(bool)
    def on_modify_none_zero_clicked(self, checked):
        self.ui.old_value_text.setEnabled(not checked)
        
    def fileitemClicked(self, currentRow):
        self.fileListIndex = currentRow
        
    def fileitemDoubleClicked(self, item=None):
        self.fileListIndex = currIndex = self.mImgList.index(item.text())
        if currIndex < len(self.mImgList):
            filename = self.mImgList[currIndex]
            if filename:
                self.loadFile(filename)

    def on_rgbValueReceived(self, r, g, b):
        self.ui.widget_rgb_resize.setValue(r, g, b)
        self.ui.widget_rgb_increase.setValue(r, g, b)

    def on_roi_received(self, rect):
        self.ui.roi_widget.setValue(rect.x(), rect.y(), rect.width(), rect.height())
        if rect.width() > 0 and rect.height() > 0:
            self.ui.img_scale_ratio.setValue(min(self.ui.new_img_height.value()/rect.height(), self.ui.new_img_width.value()/rect.width()) - 0.01) # for math floor
    
    def on_roi_changed(self, x, y, w, h):
        if w > 0 and h > 0:
            self.ui.img_scale_ratio.setValue(min(self.ui.new_img_height.value()/h, self.ui.new_img_width.value()/w) - 0.01)
         
    def scrollRequest(self, delta, orientation):
        units = - delta / (8 * 15)
        bar = self.scrollBars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * units)

    @pyqtSlot()
    def on_resize_images_clicked(self):
        dest_dir = self._open_dir()
        if not self.confirm_operation("rename files"):
            return
        if self.ui.resize_mode.currentText() == "ROI":
            if self.ui.roi_widget.roi_width() * self.ui.img_scale_ratio.value() > self.ui.new_img_width.value() or \
                    self.ui.roi_widget.roi_height() * self.ui.img_scale_ratio.value() > self.ui.new_img_height.value():
                QMessageBox.warning(self, 'warning', 'roi out of range')
                return
        data_operations.warp(self.dirname, dest_dir, resize_mode = self.ui.resize_mode.currentText(),
                        padding_color = self.ui.widget_rgb_resize.value(),
                        new_width = self.ui.new_img_width.value(),
                        new_height= self.ui.new_img_height.value(),
                        scale_ratio= self.ui.img_scale_ratio.value(), 
                        roi=self.ui.roi_widget.value(),
                        example_file_path = self.ui.resize_file.text())
        notify_operation_finished("resize images ", len(self.mImgList))
        self.reloadImg(dest_dir)
            
    @pyqtSlot()
    def on_rename_files_clicked(self):
        if not self.confirm_operation("rename files"):
            return
        name_prefix = self.ui.prefix_list.currentText()    
        if name_prefix == 'self-defined':
            name_prefix, _ = QInputDialog.getText(self, "text", 'please input file name prefix:')

        split_dir_to_images_labels(self.dirname)
        voc_data_checker.rename_jpg_files(self.dirname, name_prefix, self.ui.start_idx.value())
        notify_operation_finished("rename images ", len(self.mImgList))
        self.reloadImg(self.dirname)
        
    @pyqtSlot()
    def on_augment_data_clicked(self):
        dest_dir = self._open_dir()
        if len(dest_dir) == 0:
            return
        data_operations.augment(self.dirname, dest_dir, 
                                self.ui.widget_brightness.value(), 
                                self.ui.widget_contrast.value(),
                                self.ui.widget_scale.value(),
                                self.ui.widget_rotation.value(),
                                self.ui.widget_translation.value(),
                                self.ui.widget_rgb_increase.value(),
                                self.ui.augment_times.value(),
                                self.ui.remain_ratio_in_aug.value())
        notify_operation_finished("augment data ", len(self.mImgList))
        self.reloadImg(dest_dir)          
        
    def _open_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Open Directory', self.lastOpenDir,
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)

        self.lastOpenDir = dir_path
        return dir_path
    
    def verify_dir_path(self):
        if self.dirname is None or len(self.mImgList) == 0:
            QMessageBox.warning(self, 'warning', 'Please choose src dir first')
            return False
        return True
    
    def confirm_operation(self, operation = None):
        if not self.verify_dir_path():
            return
        return QMessageBox.Yes == QMessageBox.question(None,
                                                       'question', 
                                                       'Confirm ' + operation + " for " + str(len(self.mImgList)) + " files?",
                                                       QMessageBox.Yes | QMessageBox.Cancel)
  
    def loadFile(self, filePath=None):
        logging.info("load file:" + filePath)
        self.setWindowTitle(__appname__ + " " + self.dirname + " " + os.path.basename(filePath))

        _, extension = os.path.splitext(filePath)
        if extension == ".exr":
            logging.info("EXR files loaded, these images won't be shown on UI but can be encoded.")
            return

        with Image.open(filePath) as im:
            self.canvas.setImage(copy.deepcopy(im), calc_pixel_value=self.ui.actionChange_Pixel_Values.isChecked())
     
        exist, label_full_path = is_label_file_exist(self.dirname, filePath)
        vertex_infos = []
        label_type = "None"
        if exist:
            label_type, vertex_infos = read_label_file(label_full_path)

        if self.is_cocodataset:
            vertex_infos, category_names = read_coco_file(self.coco_parser, filePath)
            label_type = "CoCo"
            self.ui.label_info_text.setPlainText(str(self.get_label_to_num(category_names)))

        if self.is_vocdataset:
            file_name_without_suffix = os.path.splitext(os.path.split(filePath)[1])[0]
            jpeg_dir_path = os.path.split(filePath)[0]
            voc_dir_path = os.path.split(jpeg_dir_path)[0]
            segmentationclass_file_path = os.path.join(voc_dir_path, 'SegmentationClass', file_name_without_suffix + '.png')

            label_type = "Voc"
            self.canvas.mask_path = segmentationclass_file_path

        self.ui.dataset_type.setText("Label Type: " + label_type)
        self.canvas.loadPixmap(QPixmap(filePath), vertex_infos)

    def scanAllImages(self, folderPath):
        image_exist_path = find_images_exist_path(folderPath)
        images = []

        files = os.listdir(image_exist_path)
        reg = r"^((?!depth).)*([0-9]+).\b(?:jpeg|jpg|png|bmp|exr)\b"
        for file in files:
            match = re.search(reg, file.lower())
            if match:
                relatviePath = os.path.join(image_exist_path, file)
                path = os.path.abspath(relatviePath)
                images.append(path)
        try:
            images.sort(key=lambda x:int(x.split('.')[0].split('_')[-1]))
        except ValueError:
            #for image with random name, not like xxx_00.jpg
            images.sort(key=lambda x: x.lower())
        return images

    def openDir(self, _value=False):
        dir_path = self._open_dir()
        if dir_path == "":
            return
        self.is_cocodataset = is_coco_dataset(dir_path)
        self.is_vocdataset = is_voc_dataset(dir_path)
        self.canvas.mask_path = ""
        if self.is_cocodataset:
            self.scan_dataset(dir_path)
        elif self.is_vocdataset:
            self.scan_voc_dataset(dir_path)
        else:
            self.reloadImg(dir_path)

    def openPrevImg(self, _value=False):
        if len(self.mImgList) <= 0:
            return

        self.fileListIndex -= 1
        self.fileListIndex = max(0, min(self.fileListIndex, len(self.mImgList)-1))
        self.loadFile(self.mImgList[self.fileListIndex])

    def openNextImg(self, _value=False):
        if len(self.mImgList) <= 0:
            return
        self.fileListIndex += 1
        self.fileListIndex = max(0, min(self.fileListIndex, len(self.mImgList)-1))
        self.loadFile(self.mImgList[self.fileListIndex])
            
    """
    @param show_sub_list: if this list is not emtpy, only show this sub list images ^ img list of dir_path 
    """        
    def reloadImg(self, dir_path, only_show_sub_list = False, show_sub_list=[]):
        if len(dir_path) == 0:
            return
        self.dirname = dir_path
        self.ui.fileList.clear()
        self.mImgList = self.scanAllImages(dir_path)
        if len(self.mImgList) <= 0:
            return
        if only_show_sub_list:
            show_sub_list = [i.replace(r'/', '\\') for i in show_sub_list]
            self.mImgList = [i.replace(r'/', '\\') for i in self.mImgList]
            self.mImgList = list(set(show_sub_list).intersection(self.mImgList))
            self.mImgList.sort()
        self.ui.fileList.clear()
        for imgPath in self.mImgList:
            item = QListWidgetItem(imgPath)
            self.ui.fileList.addItem(item)
        self.fileListIndex = 0
        if self.mImgList:
            self.loadFile(self.mImgList[0])

    def scan_dataset(self, json_path):
        choose_json_dialog = option.OptionDialog(parent=None, name="choose_json_file", options=os.listdir(os.path.join(json_path, "annotations")))
        if QDialog.Rejected == choose_json_dialog.exec():
            return
        
        json_file_name = choose_json_dialog.current_option()
        json_full_path = os.path.join(json_path, "annotations", json_file_name)
        image_exist_path = os.path.join(json_path, os.path.splitext(json_file_name)[0].split('_')[1])

        self.coco_parser = CocoParser(json_full_path)
        self.coco_parser.gather_image_names()

        if json_full_path.endswith("minival2014.json"):#minival or valminusminival
            val_path = os.path.join(os.path.dirname(image_exist_path),'val2014')
            self.reloadImg(val_path, True, [os.path.join(val_path, i) for i in self.coco_parser.get_img_names()])
        else:
            self.reloadImg(image_exist_path)


    def scan_voc_dataset(self, voc_path):
        image_exist_path = os.path.join(voc_path, "JPEGImages")
        self.reloadImg(image_exist_path)
        
    def openFile(self, _value=False):
        filename = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, ".")
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.loadFile(filename)     
                
    def closeEvent(self, *args, **kwargs):
        settings.write_settings("setting.ini", self.ui.__dict__)

    def get_label_to_num(self, category_names):
        category_names_nums = []
        for category_name in set(category_names):
            category_num = category_names.count(category_name)
            category_names_nums.append((category_name, category_num))
        return category_names_nums

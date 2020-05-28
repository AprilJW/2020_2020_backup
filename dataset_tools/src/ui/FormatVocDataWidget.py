from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import pyqtSlot
import logging

import ui.Ui_FormatVocDataWidget as ui
from libs import voc_data_checker
from libs import format_voc_data

class FormatVocDataWidget(QWidget):
    def __init__(self, dir_path = None):
        QWidget.__init__(self)
        self.ui = ui.Ui_FormatVocDataWidget()
        self.ui.setupUi(self)
        self.ui.widget_file_path.setName("File Path")
        self.ui.widget_file_path.setPath(dir_path)
         
    @pyqtSlot()
    def on_check_label_clicked(self):
        dir_path = self.ui.widget_file_path.value()
        label_to_num = voc_data_checker.get_label_info(dir_path)
        logging.info("check label:{0}".format(label_to_num))
        self.ui.labelList.setRowCount(len(label_to_num))

        index = 0
        for label in label_to_num:
            label_item = QTableWidgetItem(label)
            label_item.setFlags(label_item.flags() ^ Qt.ItemIsEditable)
            self.ui.labelList.setItem(index, 0, label_item)

            rename_item = QTableWidgetItem(label)
            rename_item.setFlags(rename_item.flags() |
                                 Qt.ItemIsEditable)
            self.ui.labelList.setItem(index, 1, rename_item)

            print('label', label, 'num', label_to_num[label])
            num_item = QTableWidgetItem(str(label_to_num[label]))
            num_item.setFlags(num_item.flags() ^ Qt.ItemIsEditable)
            self.ui.labelList.setItem(index, 2, num_item)
            index += 1
            
    @pyqtSlot()
    def on_rename_label_clicked(self):
        old_to_new_label = {}
        for i in range(self.ui.labelList.rowCount()):
            old_label = self.ui.labelList.item(i, 0).text()
            new_label = self.ui.labelList.item(i, 1).text()
            old_to_new_label[old_label] = new_label

        logging.info('rename label:{0}'.format(old_to_new_label))
        dir_path = self.ui.widget_file_path.value()
        voc_data_checker.rename_label(dir_path, old_to_new_label)

        logging.info("rename label finished")
        QMessageBox.information(self, "Info", "rename label finished")
        
    @pyqtSlot()
    def on_check_data_clicked(self):
        dir_path = self.ui.widget_file_path.value()
        voc_data_checker.check_data(dir_path)
        logging.info("check jpg xml finished")

    @pyqtSlot()
    def on_format_data_clicked(self):
        dir_path = self.ui.widget_file_path.value()
        voc_formatter = format_voc_data.FormatToVOCData(
            dir_path, self.ui.train_test_ratio.value() / 100, self.ui.train_val_ratio.value() / 100,
                      self.ui.pos_neg_ratio.value() / 100)
        voc_formatter.start_format()
        QMessageBox.information(self, "Info", "format data completed")
        
    def setSrcPath(self, dir_path):
        self.ui.widget_file_path.setPath(dir_path)

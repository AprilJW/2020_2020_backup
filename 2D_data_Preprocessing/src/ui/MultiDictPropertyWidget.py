# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MultiDictPropertyWidget.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import logging

from ui.property.PropertyToWidget import *


def _check_dict_satisfied(dic={}, sub_dict_keys=[]):
    for val in dic.values():
        if type(val) is not dict:
            return False
        else:
            for sub_dict_key in sub_dict_keys:
                if sub_dict_key not in val.keys():
                    return False
    return True


class MultiDictPropertyWidget(QWidget):
    valChanged = pyqtSignal()
    cellClicked = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.property_widgets = {}
        self.current_dict_key = ''
        self.selected_current_dict_key=[]
        QMetaObject.connectSlotsByName(self)

    @pyqtSlot()
    def on_item_changed(self):
        self.valChanged.emit()

    @pyqtSlot(int, int)
    def on_tableWidget_cellClicked(self, row, col):
        logging.info("cell"+str(row) + str(col)+" selected")
        self.current_dict_key = self.tableWidget.item(row, 0).text()
        # user can only select first column cells
        self.selected_current_dict_key = [i.text() for i in self.tableWidget.selectedItems()]
        self.cellClicked.emit(self.tableWidget.item(row, 0).text())

    def clear_cell_selections(self):
        self.selected_current_dict_key.clear()

    def bind_multi_dict_to_widget(self, dic={}, sub_dict_keys=[], read_only_keys=["SeedNum"]):
        self.tableWidget.clear()
        self.property_widgets.clear()
        if not _check_dict_satisfied(dic=dic, sub_dict_keys=sub_dict_keys):
            logging.info('sub_dict keys is not matched')
            return
        self.tableWidget.setColumnCount(len(sub_dict_keys) + 1)
        self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem('type'))
        for sub_dict_key_idx in range(len(sub_dict_keys)):
            item = QTableWidgetItem(sub_dict_keys[sub_dict_key_idx])
            self.tableWidget.setHorizontalHeaderItem(sub_dict_key_idx + 1, item)
        self.tableWidget.setRowCount(len(dic.keys()))
        dic_idx = 0
        logging.info(str(dic))
        logging.info(str(sub_dict_keys))
        for key, sub_dic in dic.items():
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() ^ Qt.ItemIsEditable)
            self.tableWidget.setItem(dic_idx, 0, key_item)
            self.property_widgets[key] = []
            for sub_idx in range(len(sub_dict_keys)):
                self.property_widgets[key].append(
                    type_to_qwidget[type(sub_dic[sub_dict_keys[sub_idx]])](property_key=sub_dict_keys[sub_idx],
                                                                           key_to_val=sub_dic, read_only=any(
                            sub_dict_keys[sub_idx] == key for key in read_only_keys)))
                self.tableWidget.setCellWidget(dic_idx, sub_idx + 1, self.property_widgets[key][-1].widget)
                self.property_widgets[key][-1].valChanged.connect(self.on_item_changed)
            dic_idx += 1

    def column_count(self):
        return self.tableWidget.columnCount()

    def show_column(self, col, show):
        if show:
            self.tableWidget.showColumn(col)
        else:
            self.tableWidget.hideColumn(col)

    def set_column_enable(self,col,isEnable=False):
        for row in range(self.tableWidget.rowCount()):
            self.set_cell_enable(row,col,isEnable)

    def set_cell_enable(self, row, col,isEnable=False):
        self.tableWidget.cellWidget(row, col).setEnable(isEnable)

    def set_cell_value(self, row, col, value):
        self.tableWidget.cellWidget(row, col).setValue(value)

    def get_cell_value(self, row, col):
        return self.tableWidget.cellWidget(row, col).value()

    def get_rows(self):
        row_items = []
        for i in range(self.tableWidget.rowCount()):
            row_items.append(self.tableWidget.item(i, 0))
        return row_items

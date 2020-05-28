# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DictPropertyListTableWidget.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost if you convert this file from .ui!
#
# WARNING! Don't convert from .ui directly! Otherwise hand-written funcs will be lost!

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ui.ListWidget import ListWidget
from util.property_utils import gen_properties_template, gen_item_order_and_desc


def _check_dict_satified(dic={}):
    for val in dic.values():
        if type(val) is not dict:
            return False
    return True

def _get_rid_of_key1(template_dic):
    new_dic = {}
    for key1 in template_dic.keys():
        for key2 in template_dic[key1].keys():
            new_dic[key2] = template_dic[key1][key2]
    return new_dic

class DictPropertyListTableWidget(QWidget):
    """
       using to display and modify dict which like {key:{sub_key:value}}, using DictPropertyWidget
    """
    valChanged = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listWidget = ListWidget(self)
        self.listWidget.setObjectName("listWidget")
        self.horizontalLayout.addWidget(self.listWidget)
        self.widget = DictPropertyWidget(self)
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.horizontalLayout.setStretch(0, 100)
        self.horizontalLayout.setStretch(1, 300)
        self.dic = {}  # {key:{param_key:value}}
        self.property_template = None
        self.item_tooltip = None
        self.widget.valChanged.connect(self.on_valChanged)
        QMetaObject.connectSlotsByName(self)

    @pyqtSlot(QListWidgetItem)
    def on_listWidget_itemActivated(self, item):
        self.listWidget.setCurrentItem(item)
        self.widget.bind_dict_to_widget(self.dic[item.text()], _get_rid_of_key1(self.property_template))

    @pyqtSlot()
    def on_valChanged(self):
        for key in self.dic.keys():
            item = self.listWidget.getItem(key)
            if item is not None and "is_used" in self.dic[key].keys():
                try:
                    self.listWidget.setItemSelected(item, self.dic[key]["is_used"])
                except:
                    pass
        self.valChanged.emit()
        
    def set_properties(self, property_template_path, order_tooltip_path):
        self.property_template = gen_properties_template(property_template_path)
        self.item_tooltip = gen_item_order_and_desc(order_tooltip_path)[1]

    def bind_dict(self, key_orders=[], dic={}):
        self.listWidget.clear()
        if not _check_dict_satified(dic=dic):
            print('dic is not satified for', self.__class__)
            return
        self.dic = dic
        if len(key_orders) == 0:
            key_orders = dic.keys()
        for list_key in key_orders:
            _item = QListWidgetItem(list_key)
            if self.item_tooltip:
                _item.setToolTip(self.item_tooltip.get(list_key))
            self.listWidget.addItem(_item)
        self.listWidget.setCurrentItem(self.listWidget.item(0))
        self.listWidget.itemActivated.emit(self.listWidget.currentItem())
        self.on_valChanged()  # highlight selected operator

    def bind_operators(self, operators=[]):
        pass


from ui.DictPropertyWidget import DictPropertyWidget

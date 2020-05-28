# from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import logging

from ui.property.PropertyToWidget import *


class DictPropertyWidget(QWidget):
    """
        display and modify dict which like {key:value}
        value's type define in propertyToWidget
    """
    valChanged = pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(0)
        item = QTableWidgetItem('property')
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem('value')
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.property_widgets = []  # widget list
        QMetaObject.connectSlotsByName(self)

    def on_item_changed(self):
        self.valChanged.emit()

    def bind_dict_to_widget(self, dic={}, property_template={}):
        # for row in range(self.tableWidget.rowCount()):
        #     self.tableWidget.removeRow(row)
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.property_widgets.clear()
        # subtract params that are necessary for users
        display_keys = [x for x in dic.keys() if x not in dic.get("not_display",'[]')]
        self.tableWidget.setRowCount(len(display_keys))

        idx = 0
        for key in sorted(display_keys):
            value = dic[key]
            widget_type = type_to_qwidget.get(type(value))
            if not widget_type:
                logging.warning("%s not supported" % key)
                continue
            
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() ^ Qt.ItemIsEditable)
            self.tableWidget.setItem(idx, 0, key_item)
            
            property_info = property_template[key]
            property_widget = widget_type(property_key=key, key_to_val=dic,
                                          single_step=property_info.get("single_step", 1),
                                          maximum=property_info.get("maximum", None),
                                          minimum=property_info.get("minimum", None),
                                          decimals=property_info.get("decimals", 2),
                                          tool_tip=property_info.get("tool_tip", ""))
            self.property_widgets.append(property_widget)
            self.tableWidget.setCellWidget(idx, 1, self.property_widgets[-1].widget)
            self.property_widgets[idx].valChanged.connect(self.on_item_changed)
            idx += 1

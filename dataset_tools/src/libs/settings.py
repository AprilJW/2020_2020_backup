from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

def toBoolean(str):
    return True if str == "true" else False

def write_settings(file_name, dict):
    setting = QSettings(file_name, QSettings.IniFormat)
    for key in dict:
        if isinstance(dict[key], QLineEdit):
            setting.setValue(dict[key].objectName(), dict[key].text())

        if isinstance(dict[key], QSpinBox):
            setting.setValue(dict[key].objectName(), dict[key].value())
            
        if isinstance(dict[key], QDoubleSpinBox):
            setting.setValue(dict[key].objectName(), dict[key].value())
            
        if isinstance(dict[key], QCheckBox):
            setting.setValue(dict[key].objectName(), dict[key].isChecked())
                
        if isinstance(dict[key], QComboBox):
            setting.setValue(dict[key].objectName(), dict[key].currentText())
                  
        if isinstance(dict[key], QDockWidget):
            setting.setValue(dict[key].objectName(), dict[key].isVisible())
            
        elif isinstance(dict[key], QAction):
            setting.setValue(dict[key].objectName(), dict[key].isChecked())
            
def add_setting(setting, key, value):
    setting.setValue(key, value)  
                
def load_settings(file_name, ui):
    setting = QSettings(file_name, QSettings.IniFormat)
    keys=setting.allKeys()
    for key in keys:
        key_attr = None
        try:
            key_attr = getattr(ui, key)
        except AttributeError:
            pass
        if isinstance(key_attr, QLineEdit):
            key_attr.setText(setting.value(key))
        elif isinstance(key_attr, QSpinBox):
            key_attr.setValue(int(setting.value(key)))
        elif isinstance(key_attr, QDoubleSpinBox):
            key_attr.setValue(float(setting.value(key)))
        elif isinstance(key_attr, QCheckBox):
            key_attr.setChecked(toBoolean(setting.value(key)))
        elif isinstance(key_attr, QComboBox):
            key_attr.setCurrentText(setting.value(key))
        elif isinstance(key_attr, QDockWidget):
            key_attr.setVisible(toBoolean(setting.value(key)))
        elif isinstance(key_attr, QAction):
            key_attr.setChecked(toBoolean(setting.value(key)))
        else:
            print("could not handle: %s"  % key)
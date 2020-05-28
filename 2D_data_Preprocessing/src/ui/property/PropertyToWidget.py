from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from ui.BrowseFilePath import BrowseFilePath
from ui.BrowseFilePath import BrowseDirPath
from ui.property.ProcessorProperty import DirPath
from ui.SpinBoxWidget import *
from ui.property.ProcessorProperty import FilePath
from ui.ComboBoxWidget import ComboBox
from ui.property.ProcessorProperty import EnumOpts


class PropertyToWidget(QObject):
    valChanged = pyqtSignal()

    def __init__(self, widget = None, property_key=None, key_to_val=None, read_only=False, tool_tip = "", **kwargs):
        super().__init__()
        self.property_key = property_key
        self.key_to_val = key_to_val
        self.read_only = read_only
        self.widget = widget
        self.widget.setToolTip(tool_tip)
        #print("self.key_to_val", self.key_to_val)
    def on_val_change(self, val):
        self.key_to_val[self.property_key] = val
        self.valChanged.emit()

class BoolToCheckbox(PropertyToWidget):
    def __init__(self, **kwargs):
        super().__init__(widget = QCheckBox(), **kwargs)
        self.widget.setChecked(self.key_to_val[self.property_key])
        self.widget.stateChanged.connect(self.on_val_change)

    def on_val_change(self, val):
        self.key_to_val[self.property_key] = val == Qt.Checked
        self.valChanged.emit()


class IntToSpinBox(PropertyToWidget):
    def __init__(self, single_step=1, maximum=1000000, minimum=-1000000, **kwargs):
        super().__init__(widget = SpinBoxWidget(), **kwargs)
        self.widget.setReadOnly(self.read_only)
        self.widget.setFocusPolicy(Qt.StrongFocus)
        self.widget.setMinimum(minimum)
        self.widget.setMaximum(maximum)
        self.widget.setSingleStep(single_step)
        self.widget.setValue(self.key_to_val[self.property_key])
        self.widget.valueChanged.connect(self.on_val_change)


class DoubleToDoubleSpinBox(PropertyToWidget):
    def __init__(self, single_step=0.1, maximum=100000.0, minimum=-100000.0, decimals=2, **kwargs):
        super().__init__(widget = DoubleSpinBoxWidget(), **kwargs)
        self.widget.setReadOnly(self.read_only)
        self.widget.setFocusPolicy(Qt.StrongFocus)
        self.widget.installEventFilter(self)
        self.widget.setMinimum(minimum)
        self.widget.setMaximum(maximum)
        self.widget.setSingleStep(single_step)
        self.widget.setDecimals(decimals)
        self.widget.setValue(self.key_to_val[self.property_key])
        self.widget.valueChanged.connect(self.on_val_change)


class StringToLineEdit(PropertyToWidget):
    def __init__(self, **kwargs):
        super().__init__(widget = QLineEdit(), **kwargs)
        self.widget.setText(self.key_to_val[self.property_key])
        self.widget.textChanged.connect(self.on_val_change)


class PathToBrowseFilePath(PropertyToWidget):
    def __init__(self, **kwargs):
        super().__init__(widget = BrowseFilePath(self), **kwargs)
        self.widget.set_path(self.key_to_val[self.property_key]())
        self.widget.valChanged.connect(self.on_val_change)

    def on_val_change(self, val):
        self.key_to_val[self.property_key].file_path = val
        self.valChanged.emit()


class PathToBrowseDirPath(PropertyToWidget):
    def __init__(self, **kwargs):
        super().__init__(widget = BrowseDirPath(self), **kwargs)
        self.widget.set_path(self.key_to_val[self.property_key]())
        self.widget.valChanged.connect(self.on_val_change)

    def on_val_change(self, val):
        self.key_to_val[self.property_key].dir_path = val
        self.valChanged.emit()


class EnumListToComboBox(PropertyToWidget):
    def __init__(self, **kwargs):
        super().__init__(widget = ComboBox(self), **kwargs)
        self.widget.add_opts(self.key_to_val[self.property_key].enum_list)
        self.widget.valChanged.connect(self.on_val_change)
        self.widget.setCurrentText(self.key_to_val[self.property_key].selected_opt)

    def on_val_change(self):
        self.key_to_val[self.property_key].selected_opt = self.widget.current_opt()
        self.valChanged.emit()


type_to_qwidget = {int: IntToSpinBox, float: DoubleToDoubleSpinBox, bool: BoolToCheckbox, str: StringToLineEdit,
                   DirPath: PathToBrowseDirPath, FilePath: PathToBrowseFilePath, EnumOpts: EnumListToComboBox}

str_to_type = {t.__name__: t for t in [str, int, DirPath, FilePath, EnumOpts, bool, float]}
str_to_type["list"] = str

# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets

class OptionDialog(QtWidgets.QDialog):
    def __init__(self, parent, name, options = None):
        super(QtWidgets.QDialog, self).__init__()
        self.setObjectName(name + " Dialog")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(self)
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setTitle(name)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.options = QtWidgets.QComboBox(self.groupBox)
        self.options.setObjectName("options")
        self.set_options(options)
        self.verticalLayout.addWidget(self.options)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        QtCore.QMetaObject.connectSlotsByName(self)
        
    def current_option(self):
        return self.options.currentText()
    
    def set_options(self, options):
        for option in options:
            self.options.addItem(option)
        self.options.setCurrentIndex(0)
        


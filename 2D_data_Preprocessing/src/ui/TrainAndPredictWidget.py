from PyQt5 import QtCore
from PyQt5.Qt import QMessageBox, QFileDialog, QListWidgetItem
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QTableWidgetItem

import os
from ui import UI_TrainAndPredictWidget as ui

from train_predict import train_helper, predict_helper
from train_predict.train_helper import TrainHelper

class TrainAndPredictWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__()
        self.ui = ui.Ui_TrainAndPredictWidget()
        self.ui.setupUi(self)
        self.lastOpenDirPath = os.path.abspath(os.path.expanduser("~"))

    @pyqtSlot()
    def on_browse_model_clicked(self):
        self.ui.modelPath.setText(self._open_dir())

    @pyqtSlot()
    def on_browse_merge_clicked(self):
        self.ui.mergePath.setText(self._open_dir())

    @pyqtSlot()
    def on_browse_predict_clicked(self):
        self.ui.predictPath.setText(self._open_dir())

    @pyqtSlot()
    def on_save_predict_clicked(self):
        predict_path = os.path.abspath(os.path.expanduser(self.ui.predictPath.text()))
        model_path = os.path.abspath(os.path.expanduser(self.ui.modelPath.text()))
        predict_helper.PredictHelper(self.ui.ComboBox_modelType_predict.currentText(), model_path, predict_path).start_predicting()
        print("predict and save result to xml finished")

    @pyqtSlot()
    def on_calculate_mAP_clicked(self):
        predict_path = os.path.abspath(os.path.expanduser(self.ui.predictPath.text()))
        model_path = os.path.abspath(os.path.expanduser(self.ui.modelPath.text()))
        mAP = predict_helper.PredictHelper(model_path, predict_path).calculate_mAP()
        print('mAP', mAP)
        self.ui.mAP.setValue(mAP)
        mAP_filepath = os.path.join(predict_path, 'mAP.txt')
        with open(mAP_filepath, 'w+') as mAP_file:
            mAP_file.write('%f' % mAP)
        print("calculating mAP done")

    @pyqtSlot()
    def on_browse_train_clicked(self):
        self.ui.trainPath.setText(self._open_dir())

    @pyqtSlot()
    def on_browse_weight_clicked(self):
        self.ui.weightPath.setText(self._open_file("*.h5"))

    @pyqtSlot()
    def on_start_train_clicked(self):
        train_path = os.path.abspath(os.path.expanduser(self.ui.trainPath.text()))
        weight_path = os.path.abspath(os.path.expanduser(self.ui.weightPath.text()))
        train_helper = TrainHelper(self.ui.modelType.currentText(), train_path, weight_path, self.ui.epoches.text(), self.ui.check_period.text())
        train_helper.start_predicting()
        
    def _open_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Open Directory', self.lastOpenDirPath,
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)

        self.lastOpenDirPath = dir_path
        return dir_path
    
    def _open_file(self, filter):
        caption = 'open File'
        filters = 'File (%s)' % (filter)
        dlg = QFileDialog(self, caption, self.lastOpenDirPath, filters)
        dlg.setDefaultSuffix(filter)
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setOption(QFileDialog.DontUseNativeDialog, False)
        if dlg.exec_():
            return dlg.selectedFiles()[0]
        return ''
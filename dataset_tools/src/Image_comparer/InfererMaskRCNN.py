############################################################################
## Author: Jiading Fang
## Company: Mech-mind
############################################################################

import sys
import os
import time
import subprocess
from PyQt5.QtCore import QFile, QIODevice, QTextStream
from PyQt5.QtWidgets import (QWidget, QLineEdit, QLabel,
    QGridLayout, QApplication, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QMessageBox, QComboBox)

from Image_comparer.progressWindow import progressWindow
from Image_comparer.Comparer import Comparer
import platform

from enum import Enum

class Status(Enum):
    initial = 1
    infering = 2
    infered = 3

class Inferer(QWidget):

    def __init__(self, number_of_initial_models = 1):

        super().__init__()
        self.widget_id_generate_list = list(range(100000))
        self.widget_id_generate_list.reverse()
        plat_form = platform.system()
        if plat_form == 'Linux':
            self.default_script_path = os.path.expanduser("~/projects/MaskRCNN-Tensorflow/samples/coco/coco_infer.py")
        elif plat_form == 'Windows':
            self.default_script_path =os.path.expanduser("D:/projects/MaskRCNN-Tensorflow/samples/coco/coco_infer.py")

        self.initUI(number_of_initial_models)

        self.status = Status.initial


    def initUI(self, number_of_initial_models):

        self.widget_id_save_list = []

        # create header widgets
        self.source_image_folder_button = QPushButton('Source Image Folder')
        self.source_image_folder_lineEdit = QLineEdit()
        self.depth_image_folder_button = QPushButton('Depth Image Folder')
        self.depth_image_folder_lineEdit = QLineEdit()
        self.model_config_button = QPushButton('Model Config')
        self.model_config_lineEdit = QLineEdit()
        self.infer_script_path_button = QPushButton('Infer Script Path')
        self.infer_script_path_lineEdit = QLineEdit()

        self.color_type_label = QLabel('Color Type')
        self.color_type_combobox = QComboBox()
        self.color_type_combobox.addItem('instance')
        self.color_type_combobox.addItem('class')

        self.python_version_label = QLabel('Python Version')
        self.python_version_combobox = QComboBox()
        self.python_version_combobox.addItem('python')
        self.python_version_combobox.addItem('python2')
        self.python_version_combobox.addItem('python3')

        source_image_holder_hbox = QHBoxLayout()
        source_image_holder_hbox.addWidget(self.source_image_folder_button)
        source_image_holder_hbox.addWidget(self.source_image_folder_lineEdit)

        depth_image_holder_hbox = QHBoxLayout()
        depth_image_holder_hbox.addWidget(self.depth_image_folder_button)
        depth_image_holder_hbox.addWidget(self.depth_image_folder_lineEdit)

        model_config_hbox = QHBoxLayout()
        model_config_hbox.addWidget(self.model_config_button)
        model_config_hbox.addWidget(self.model_config_lineEdit)

        infer_script_path_hbox = QHBoxLayout()
        infer_script_path_hbox.addWidget(self.infer_script_path_button)
        infer_script_path_hbox.addWidget(self.infer_script_path_lineEdit)

        infer_settings_hbox = QHBoxLayout()
        infer_settings_hbox.addWidget(self.color_type_label)
        infer_settings_hbox.addWidget(self.color_type_combobox)
        infer_settings_hbox.addWidget(self.python_version_label)
        infer_settings_hbox.addWidget(self.python_version_combobox)

        self.header_vbox = QVBoxLayout()
        self.header_vbox.addLayout(source_image_holder_hbox)
        self.header_vbox.addLayout(depth_image_holder_hbox)
        self.header_vbox.addLayout(model_config_hbox)
        self.header_vbox.addLayout(infer_script_path_hbox)
        self.header_vbox.addLayout(infer_settings_hbox)

        self.model_path_buttons = {}
        self.model_path_lineEdits = {}
        self.save_folder_buttons = {}
        self.save_folder_lineEdits = {}
        self.delete_buttons = {}

        for which_model in range(number_of_initial_models):
            self.buttonClickedAddModel()

        self.add_model_button = QPushButton('Add Model')
        self.infer_button = QPushButton('Infer')

        # set up signals and slots for widgets
        self.source_image_folder_button.clicked.connect(self.buttonClickedGetSourceImageFolder)
        self.depth_image_folder_button.clicked.connect(self.buttonClickedGetDepthImageFolder)
        self.model_config_button.clicked.connect(self.buttonClickedGetModelConfig)
        self.infer_script_path_button.clicked.connect(self.buttonClickedGetInferScriptPath)
        self.add_model_button.clicked.connect(self.buttonClickedAddModel)
        self.infer_button.clicked.connect(self.buttonClickedInfer)

        # create window layout
        self.header_grid_layout = QGridLayout()
        self.header_button_hbox = QHBoxLayout()
        self.window_vbox = QVBoxLayout()

        # set up initial header layout
        self.header_button_hbox.addWidget(self.add_model_button)
        self.header_button_hbox.addStretch(1)
        self.header_button_hbox.addWidget(self.infer_button)

        self.window_vbox.addLayout(self.header_vbox)
        self.window_vbox.addLayout(self.header_button_hbox)

        # set up window display
        self.setLayout(self.window_vbox)
        self.setWindowTitle('Inferer')

        # infered flag
        self.infered_flag = False
        # set finished flag
        self.finished_flag = False

    def buttonClickedGetSourceImageFolder(self):

        folder_name = QFileDialog.getExistingDirectory(self, 'Select Source Image Folder')
        self.source_image_folder_lineEdit.setText(str(folder_name))

    def buttonClickedGetDepthImageFolder(self):

        folder_name = QFileDialog.getExistingDirectory(self, 'Select Depth Image Folder')
        self.depth_image_folder_lineEdit.setText(str(folder_name))

    def buttonClickedGetModelConfig(self):

        config_name = QFileDialog.getOpenFileName(self, 'Select Model Config', self.tr("*yml"))
        self.model_config_lineEdit.setText(str(config_name[0]))

    def buttonClickedGetInferScriptPath(self):

        path_name = QFileDialog.getOpenFileName(self, 'Select Infer Script', self.default_script_path)
        self.infer_script_path_lineEdit.setText(str(path_name[0]))

    def buttonClickedGetModelPath(self, widget_id):

        path_name = QFileDialog.getOpenFileName(self, 'Select Model Path')
        self.model_path_lineEdits[widget_id].setText(str(path_name[0]))

    def buttonClickedGetSaveFolder(self, widget_id):

        folder_name = QFileDialog.getExistingDirectory(self, 'Select Infer results Save Folder')
        self.save_folder_lineEdits[widget_id].setText(str(folder_name))

    def buttonClickedAddModel(self):

        widget_id = self.widget_id_generate_list.pop()

        #number_of_existing_models = len(self.model_path_buttons)
        self.widget_id_save_list.append(widget_id)

        # create new widgets
        new_model_path_button = QPushButton('Model Path')
        self.model_path_buttons[widget_id] = new_model_path_button
        new_model_path_lineEdit = QLineEdit()
        self.model_path_lineEdits[widget_id] = new_model_path_lineEdit
        new_save_folder_button = QPushButton('Save Folder')
        self.save_folder_buttons[widget_id] = new_save_folder_button
        new_save_folder_lineEdit = QLineEdit()
        self.save_folder_lineEdits[widget_id] = new_save_folder_lineEdit
        new_delete_button = QPushButton('Delete')
        self.delete_buttons[widget_id] = new_delete_button

        # set up signals and slots for new widgets
        new_model_path_button.clicked.connect(lambda: self.buttonClickedGetModelPath(widget_id))
        new_save_folder_button.clicked.connect(lambda: self.buttonClickedGetSaveFolder(widget_id))
        new_delete_button.clicked.connect(lambda: self.buttonClickedDeleteModel(widget_id))

        new_model_hbox = QHBoxLayout()

        # set up layout
        new_model_hbox.addWidget(new_model_path_button)
        new_model_hbox.addWidget(new_model_path_lineEdit)
        new_model_hbox.addWidget(new_save_folder_button)
        new_model_hbox.addWidget(new_save_folder_lineEdit)
        new_model_hbox.addWidget(new_delete_button)

        self.header_vbox.addLayout(new_model_hbox)

    def buttonClickedDeleteModel(self, widget_id):

        number_of_existing_models = len(self.model_path_buttons)

        if number_of_existing_models < 2:
            QMessageBox.warning(self, 'Error Message', 'Not enough models, you need to keep at least 1 model.')
            return 0

        removed_model_path_button = self.model_path_buttons.pop(widget_id)
        removed_model_path_lineEdit = self.model_path_lineEdits.pop(widget_id)
        removed_save_path_button = self.save_folder_buttons.pop(widget_id)
        removed_save_path_lineEdit = self.save_folder_lineEdits.pop(widget_id)
        removed_delete_button = self.delete_buttons.pop(widget_id)

        self.widget_id_save_list.remove(widget_id)
        
        self.header_vbox.removeWidget(removed_model_path_button)
        self.header_vbox.removeWidget(removed_model_path_lineEdit)
        self.header_vbox.removeWidget(removed_save_path_button)
        self.header_vbox.removeWidget(removed_save_path_lineEdit)
        self.header_vbox.removeWidget(removed_delete_button)

        removed_model_path_button.hide()
        removed_model_path_lineEdit.hide()
        removed_save_path_button.hide()
        removed_save_path_lineEdit.hide()
        removed_delete_button.hide()

    def switchFromIntialToInfering(self):
        self.status = Status.infering
        self.enabledAllButtons(False)

    def switchFromInferingToInfered(self):
        self.status = Status.infered
        self.enabledAllButtons(True)

    def switchFromInferedToInfering(self):
        self.status = Status.infering
        self.enabledAllButtons(False)
        self.infer_progress_window.hide()
        self.window_vbox.removeWidget(self.infer_progress_window)

    def enabledAllButtons(self,enabled):
        self.source_image_folder_button.setEnabled(enabled)
        self.depth_image_folder_button.setEnabled(enabled)
        self.model_config_button.setEnabled(enabled)
        self.infer_script_path_button.setEnabled(enabled)
        for model_path_button in self.model_path_buttons.values():
            model_path_button.setEnabled(enabled)
        for save_floder_button in self.save_folder_buttons.values():
            save_floder_button.setEnabled(enabled)
        for delete_button in self.delete_buttons.values():
            delete_button.setEnabled(enabled)
        self.add_model_button.setEnabled(enabled)
        self.infer_button.setEnabled(enabled)
        self.color_type_combobox.setEnabled(enabled)
        self.python_version_combobox.setEnabled(enabled)

    def buttonClickedInfer(self):

        class inferProgressWindow(progressWindow):

            def __init__(self):

                super().__init__()

                # add compare button to hbox
                self.body_button_hbox = QHBoxLayout()
                self.compare_button = QPushButton('Compare')
                self.body_button_hbox.addStretch(1)
                self.body_button_hbox.addWidget(self.compare_button)
                self.body_vbox.addLayout(self.body_button_hbox)



        if any(len(os.listdir(save_folder_lineEdit.text())) > 0 for save_folder_lineEdit in self.save_folder_lineEdits.values()):
            QMessageBox.warning(self, 'Error Message', 'Each save folder must be empty, please check if there is anything in the folder.')
            return

        if self.status is Status.initial:
            self.switchFromIntialToInfering()
        elif self.status is Status.infered:
            ret = QMessageBox.question(self, "Re-Infer Dialog", "Are you sure you want to Re-Infer?")
            if ret == QMessageBox.Yes:
               self.switchFromInferedToInfering()
            else:
                return

        # add progress window
        self.infer_progress_window = inferProgressWindow()
        self.infer_progress_window.addMultipleProgress(len(self.model_path_buttons))
        self.infer_progress_window.compare_button.clicked.connect(self.buttonClickedCompare)
        self.window_vbox.addWidget(self.infer_progress_window)

        for which_model, widget_id in enumerate(self.model_path_buttons):
            time_stamp = int(time.time()*10e6)
            config_file_name = 'config_' + str(time_stamp) + '.yml'
            current_directory = os.getcwd()
            if not os.path.isdir('configs'):
                os.mkdir('configs')
            config_file_path = os.path.join(current_directory, 'configs', config_file_name)

            error = None
            config_file = None
            try:
                config_file = QFile(config_file_path)
                if not config_file.open(QIODevice.WriteOnly):
                    raise IOError(str(config_file.errorString()))
                config_stream = QTextStream(config_file)
                config_stream.setCodec('UTF-8')
                config_stream << 'infer_settings:\n'
                config_stream << '    save_dir: ' << self.save_folder_lineEdits[widget_id].text() << '\n'
                config_stream << '    restore_from: ' << self.model_path_lineEdits[widget_id].text() << '\n'
                config_stream << '    data_dir: ' << self.source_image_folder_lineEdit.text() << '\n'
                config_stream << '    depth_dir: ' <<  self.depth_image_folder_lineEdit.text() << '\n'
                config_stream << '    model_config: ' << self.model_config_lineEdit.text() << '\n'
                config_stream << '    #color_type candidates: \'instance\',\'class\' ' << '\n'
                config_stream << '    color_type: ' << self.color_type_combobox.currentText() << '\n'

                print("Saved config file as {0}".format(config_file_path))
            except EnvironmentError as e:
                error = "Failed to save {0} because of {1}".format(config_file_name, e)
            finally:
                if config_file is not None:
                    config_file.close()
                if error is not None:
                    print(error)

            # start inference subprocess
            python_version = str(self.python_version_combobox.currentText())
            subprocess_args = python_version + ' ' + self.infer_script_path_lineEdit.text() + ' ' + config_file_path

            p = subprocess.Popen(subprocess_args, shell=True)
            number_of_source_images = len(os.listdir(self.source_image_folder_lineEdit.text()))

            while p.poll() is None:
                number_of_saved_images = len(os.listdir(self.save_folder_lineEdits[widget_id].text()))
                self.infer_progress_window.progress_bars[which_model].setValue(number_of_saved_images/number_of_source_images*100)
                QApplication.processEvents()

        QMessageBox.warning(self, 'Success Message', 'The infer process has successfully finished!')
        self.switchFromInferingToInfered()


    def buttonClickedCompare(self):
        self.infer_result_comparer = Comparer(len(self.model_path_lineEdits))
        for inferer_widget_id in self.model_path_lineEdits:
            self.infer_result_comparer.multi_select_dialog.add_one_dir(self.save_folder_lineEdits[inferer_widget_id].text())
def main():
    app = QApplication(sys.argv)
    ex = Inferer()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()

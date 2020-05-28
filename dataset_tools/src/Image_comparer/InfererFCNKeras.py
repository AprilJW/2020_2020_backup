############################################################################
## Author: Jiading Fang
## Company: Mech-mind
############################################################################

import sys
import os
import time
import subprocess
from PyQt5.QtCore import QFile, QIODevice, QTextStream
from PyQt5.QtWidgets import (QLabel, QWidget, QLineEdit,
    QGridLayout, QApplication, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QMessageBox, QComboBox)

from Image_comparer.progressWindow import progressWindow
from Image_comparer.Comparer import Comparer
import platform
class Inferer(QWidget):

    def __init__(self, number_of_initial_models = 1):

        super().__init__()
        self.widget_id_generate_list = list(range(100000))
        self.widget_id_generate_list.reverse()
        plat_form = platform.system()
        if plat_form == 'Linux':
            self.infer_script_default_path = os.path.expanduser("~/projects/fcn-keras/inference.py")
        elif plat_form == 'Windows':
            self.infer_script_default_path = os.path.expanduser("D:/projects/fcn-keras/inference.py")

        self.initUI(number_of_initial_models)

    def initUI(self, number_of_initial_models):

        self.widget_id_save_list = []

        # create header widgets
        self.source_image_list_button = QPushButton('Source Image List')
        #self.source_image_list_lineEdit = QLineEdit()
        self.source_image_list_lineEdit = QLineEdit('/home/amax/Data/20180714_medicine/file_list.txt')
        self.data_directory_button = QPushButton('Data Directory')
        #self.data_directory_lineEdit = QLineEdit()
        self.data_directory_lineEdit = QLineEdit('/home/amax/Data/20180714_medicine/20180702_medicine_highlight')
        self.label_example_path_button = QPushButton('Label Example')
        #self.label_example_path_lineEdit = QLineEdit()
        self.label_example_path_lineEdit = QLineEdit('/home/amax/Data/20180714_medicine/2007_000000.png')
        self.infer_script_button = QPushButton('Infer Script Path')
        #self.infer_script_path_lineEdit = QLineEdit()
        self.infer_script_path_lineEdit = QLineEdit('/home/amax/projects/fcn-keras/inference.py')
        self.python_version_label = QLabel('Python Version')
        self.python_version_combobox = QComboBox()
        self.python_version_combobox.addItem('python')
        self.python_version_combobox.addItem('python2')
        self.python_version_combobox.addItem('python3')

        source_image_list_hbox = QHBoxLayout()
        source_image_list_hbox.addWidget(self.source_image_list_button)
        source_image_list_hbox.addWidget(self.source_image_list_lineEdit)

        data_directory_hbox = QHBoxLayout()
        data_directory_hbox.addWidget(self.data_directory_button)
        data_directory_hbox.addWidget(self.data_directory_lineEdit)

        label_example_path_hbox = QHBoxLayout()
        label_example_path_hbox.addWidget(self.label_example_path_button)
        label_example_path_hbox.addWidget(self.label_example_path_lineEdit)

        infer_script_hbox = QHBoxLayout()
        infer_script_hbox.addWidget(self.infer_script_button)
        infer_script_hbox.addWidget(self.infer_script_path_lineEdit)
        infer_script_hbox.addWidget(self.python_version_label)
        infer_script_hbox.addWidget(self.python_version_combobox)

        #python_version_hbox = QHBoxLayout()
        #python_version_hbox.addWidget(self.python_version_label)
        #python_version_hbox.addWidget(self.python_version_combobox)

        self.header_vbox = QVBoxLayout()
        self.header_vbox.addLayout(source_image_list_hbox)
        self.header_vbox.addLayout(data_directory_hbox)
        self.header_vbox.addLayout(label_example_path_hbox)
        #self.header_vbox.addLayout(python_version_hbox)
        self.header_vbox.addLayout(infer_script_hbox)

        self.model_path_buttons = {}
        self.model_path_lineEdits = {}
        self.save_folder_buttons = {}
        self.save_folder_lineEdits = {}
        self.class_number_labels = {}
        self.class_number_lineEdits = {}
        self.delete_buttons = {}

        for which_model in range(number_of_initial_models):
            self.buttonClickedAddModel()

        self.add_model_button = QPushButton('Add Weight File')
        self.infer_button = QPushButton('Infer')

        # set up signals and slots for widgets
        self.source_image_list_button.clicked.connect(self.buttonClickedGetImageListPath)
        self.data_directory_button.clicked.connect(self.buttonClickedGetDataDirectory)
        self.label_example_path_button.clicked.connect(self.buttonClickedGetLabelExamplePath)
        self.infer_script_button.clicked.connect(self.buttonClickedGetInferScriptPath)
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
        self.setWindowTitle('FCN-Keras Inferer')

        # infered flag
        self.infered_flag = False
        # set finished flag to false
        self.finished_flag = False

    def buttonClickedGetImageListPath(self):

        list_name = QFileDialog.getOpenFileName(self, 'Select Image List txt')
        self.source_image_list_lineEdit.setText(str(list_name[0]))

    def buttonClickedGetDataDirectory(self):

        folder_name = QFileDialog.getExistingDirectory(self, 'Select Data Directory')
        self.data_directory_lineEdit.setText(str(folder_name))

    def buttonClickedGetLabelExamplePath(self):

        label_name = QFileDialog.getOpenFileName(self, 'Select Label Example Path')
        self.label_example_path_lineEdit.setText(str(label_name[0]))

    def buttonClickedGetInferScriptPath(self):

        path_name = QFileDialog.getOpenFileName(self, 'Select Infer Script', self.infer_script_default_path)
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
        new_model_path_button = QPushButton('Weight File Path')
        self.model_path_buttons[widget_id] = new_model_path_button
        new_model_path_lineEdit = QLineEdit()
        self.model_path_lineEdits[widget_id] = new_model_path_lineEdit
        new_save_folder_button = QPushButton('Save Folder')
        self.save_folder_buttons[widget_id] = new_save_folder_button
        new_save_folder_lineEdit = QLineEdit()
        self.save_folder_lineEdits[widget_id] = new_save_folder_lineEdit
        new_class_number_label = QLabel('Class number')
        new_class_number_lineEdit = QLineEdit('2')
        self.class_number_labels[widget_id] = new_class_number_label
        self.class_number_lineEdits[widget_id] = new_class_number_lineEdit
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
        new_model_hbox.addWidget(new_class_number_label)
        new_model_hbox.addWidget(new_class_number_lineEdit)
        new_model_hbox.addWidget(new_delete_button)

        self.header_vbox.addLayout(new_model_hbox)

    def buttonClickedDeleteModel(self, widget_id):

        if self.finished_flag:
            return 0

        number_of_existing_models = len(self.model_path_buttons)

        if number_of_existing_models < 2:
            QMessageBox.warning(self, 'Error Message', 'Not enough models, you need to keep at least 1 model.')
            return 0

        removed_model_path_button = self.model_path_buttons.pop(widget_id)
        removed_model_path_lineEdit = self.model_path_lineEdits.pop(widget_id)
        removed_save_path_button = self.save_folder_buttons.pop(widget_id)
        removed_save_path_lineEdit = self.save_folder_lineEdits.pop(widget_id)
        removed_class_number_label = self.class_number_labels.pop(widget_id)
        removed_class_number_lineEdit = self.class_number_lineEdits.pop(widget_id)
        removed_delete_button = self.delete_buttons.pop(widget_id)

        self.widget_id_save_list.remove(widget_id)

        self.header_vbox.removeWidget(removed_model_path_button)
        self.header_vbox.removeWidget(removed_model_path_lineEdit)
        self.header_vbox.removeWidget(removed_save_path_button)
        self.header_vbox.removeWidget(removed_save_path_lineEdit)
        self.header_vbox.removeWidget(removed_class_number_label)
        self.header_vbox.removeWidget(removed_class_number_lineEdit)
        self.header_vbox.removeWidget(removed_delete_button)

        removed_model_path_button.hide()
        removed_model_path_lineEdit.hide()
        removed_save_path_button.hide()
        removed_save_path_lineEdit.hide()
        removed_class_number_label.hide()
        removed_class_number_lineEdit.hide()
        removed_delete_button.hide()

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

        if self.infered_flag:
            re_infer_flag = QMessageBox.question(self, "Re-Infer Dialog", "Are you sure you want to Re-Infer?")
            if re_infer_flag == QMessageBox.Yes:
                self.infer_progress_window.hide()
                self.window_vbox.removeWidget(self.infer_progress_window)
            else:
                return 0

        if any(len(os.listdir(save_folder_lineEdit.text())) > 0 for save_folder_lineEdit in self.save_folder_lineEdits.values()):
            QMessageBox.warning(self, 'Error Message', 'Each save folder must be empty, please check if there is anything in the folder.')
            return 0

        folder_name_list = [folder_lineEdit.text() for folder_lineEdit in self.save_folder_lineEdits.values()]
        if any([folder_name_list[i] == folder_name_list[i+1] for i in range(len(folder_name_list)-1)]):
            QMessageBox.warning(self, 'Error Message', 'Each save folder must be different, please check if there are any duplicate folders')
            return 0

        if self.source_image_list_lineEdit.text() == '':
            QMessageBox.warning(self, 'Error Message', 'Image list txt should not be empty.')
            return 0

        if self.data_directory_lineEdit.text() == '':
            QMessageBox.warning(self, 'Error Message', 'Data directory should not be empty.')
            return 0

        if self.label_example_path_lineEdit.text() == '':
            QMessageBox.warning(self, 'Error Message', 'label example picture should not be empty')
            return 0

        if self.infer_script_path_lineEdit.text() == '':
            QMessageBox.warning(self, 'Error Message', 'Infer script should not be empty.')
            return 0

        # infered flag set to true
        self.infered_flag = True
        # set finished flag
        self.finished_flag = False

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
                config_stream << 'inference_paths:\n'
                config_stream << '    inference_img_list_path: ' << self.source_image_list_lineEdit.text() << '\n'
                config_stream << '    data_dir: ' << self.data_directory_lineEdit.text() << '\n'
                config_stream << '    weight_file_path: ' << self.model_path_lineEdits[widget_id].text() << '\n'
                config_stream << '    label_example_path: ' << self.label_example_path_lineEdit.text() << '\n'
                config_stream << '    save_dir: ' << self.save_folder_lineEdits[widget_id].text() << '\n'
                config_stream << 'classes_num:\n' << '    classes_num_specific: ' << self.class_number_lineEdits[widget_id].text()
                if not os.path.isdir('logs'):
                    os.mkdir('logs')
                #config_stream << '    model_log_dir: ' << os.path.join(os.getcwd(), 'logs')
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
            image_list_txt = open(self.source_image_list_lineEdit.text(),'r')
            number_of_source_images = len(image_list_txt.readlines())
            #number_of_source_images = len(os.listdir(self.source_image_folder_lineEdit.text()))

            while p.poll() is None:
                number_of_saved_images = len(os.listdir(self.save_folder_lineEdits[widget_id].text()))
                self.infer_progress_window.progress_bars[which_model].setValue(number_of_saved_images/number_of_source_images*100)
                QApplication.processEvents()

        QMessageBox.warning(self, 'Success Message', 'The infer process has successfully finished!')
        self.finished_flag = True


    def buttonClickedCompare(self):

        if not self.finished_flag:
            QMessageBox.warning(self, 'Error Message', 'The infer process has not finished, please kindly wait.')
            return 0
        else:
            self.infer_result_comparer = Comparer(len(self.model_path_lineEdits))
            for inferer_widget_id in self.model_path_lineEdits:
                self.infer_result_comparer.multi_select_dialog.add_one_dir(self.save_folder_lineEdits[inferer_widget_id].text())

def main():
    app = QApplication(sys.argv)
    ex = Inferer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

    

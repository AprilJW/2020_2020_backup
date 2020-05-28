from PyQt5.QtWidgets import *
import os, subprocess


class Inferer(QWidget):
    def __init__(self):
        super().__init__()
        self.image_dir_label = QLabel("Image Dir")
        self.image_dir_edit = QLineEdit()
        self.image_dir_button = QPushButton("...")
        self.model_dir_label = QLabel("Model Dir")
        self.model_dir_edit = QLineEdit()
        self.model_dir_button = QPushButton("...")
        self.predit_button = QPushButton("Predit and save result to xml")
        self.is_covert_model = QLabel("Convert model")
        self.radio_button_yes = QRadioButton("Yes")
        self.radio_button_yes.setChecked(True)
        self.radio_button_no = QRadioButton("No")

        image_hlayout = QHBoxLayout()
        image_hlayout.addWidget(self.image_dir_label)
        image_hlayout.addWidget(self.image_dir_edit)
        image_hlayout.addWidget(self.image_dir_button)
        model_hlayout = QHBoxLayout()
        model_hlayout.addWidget(self.model_dir_label)
        model_hlayout.addWidget(self.model_dir_edit)
        model_hlayout.addWidget(self.model_dir_button)
        predit_hlayout = QHBoxLayout()
        predit_hlayout.addWidget(self.predit_button)

        convert_model_hlayout = QHBoxLayout()
        convert_model_hlayout.addWidget(self.is_covert_model)
        convert_model_hlayout.addWidget(self.radio_button_yes)
        convert_model_hlayout.addWidget(self.radio_button_no)

        vbxlayout = QVBoxLayout()
        vbxlayout.addLayout(image_hlayout)
        vbxlayout.addLayout(model_hlayout)
        vbxlayout.addLayout(convert_model_hlayout)
        vbxlayout.addLayout(predit_hlayout)
        self.setLayout(vbxlayout)
        self.predit_button.clicked.connect(self.start_predit)
        self.image_dir_button.clicked.connect(self.select_image_dir)
        self.model_dir_button.clicked.connect(self.select_model_dir)

    def select_image_dir(self):
        image_dir = QFileDialog.getExistingDirectory(self, "open image dir")
        if image_dir == "":
            return
        self.image_dir_edit.setText(image_dir)

    def select_model_dir(self):
        model_path = QFileDialog.getOpenFileName(self, "select model")[0]
        if model_path == "":
            return
        self.model_dir_edit.setText(model_path)

    def start_predit(self):
        weight_path = self.model_dir_edit.text()
        exec_cmd = ""
        if self.radio_button_yes.isChecked():
            index = weight_path.find(".h5")
            target_path = weight_path[: index] + "_infer.h5"
            convert_model_script = os.path.abspath('../../RetinaNet/keras_retinanet/bin/convert_model.py')
            exec_cmd += 'python ' + convert_model_script + ' ' + weight_path + ' ' + target_path + "&&"
            weight_path = target_path
        script = os.path.abspath('../../RetinaNet/keras_retinanet/bin/inference.py')
        exec_cmd += 'python ' + script
        exec_cmd += ' -p ' + self.image_dir_edit.text()
        exec_cmd += ' --model_path ' + weight_path
        exec_cmd += ' --class_path ' + os.path.join(os.path.dirname(weight_path), 'class.json')
        subprocess.Popen(exec_cmd, shell=True)


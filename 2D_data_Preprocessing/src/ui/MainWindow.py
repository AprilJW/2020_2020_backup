import copy
import json
import os
import sys
import cv2
import logging
import numpy as np

from PyQt5.Qt import QMessageBox, QFileDialog, QListWidgetItem, QFont, \
    QInputDialog, QLineEdit, QEvent, QWidget, QAbstractSpinBox, QSpinBox
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow
from cutout.ImageGallery import ImageGallery

from generate_data import DataGenerator2D, generate_helper
from generate_data.GenerateConfig import GenerateConfig
from generate_data.JSONEncoder import ExtendJSONEncoder
from util import img_process_util

from train_predict import train_helper
from ui import UI_MainWindow as ui
from util import util

sys.path.append(os.path.abspath(os.path.expanduser('../../../dataset_tools/src')))
from libs import settings
from libs import voc_data_checker

from util.property_utils import gen_default_settings_with_type, gen_properties_template, gen_item_order_and_desc

is_close_image = False
image_show = None
select_points = []
order_tooltip_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "projects/order_tooltip.json"))

property_template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "property_template"))


STATUS_STYLE_OK = "QLabel {color : green; }"
STATUS_STYLE_WARNING = "QLabel {color : red; }"


def notify_operation_error(operation, msg):
    QMessageBox.warning(None, 'warning', operation + ': ' + msg)


def verify_file_path(file_path, is_dir=True):
    if len(file_path) == 0:
        QMessageBox.warning(None, 'warning', 'file path empty')
        return False
    if is_dir and not os.path.isdir(file_path):
        QMessageBox.warning(None, 'warning', 'dir not exist')
        return False
    if not is_dir and not os.path.isfile(file_path):
        QMessageBox.warning(None, 'warning', 'file not exist')
        return False
    return True


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = ui.Ui_MainWindow()
        self.ui.setupUi(self)
        settings.load_settings("setting.ini", self.ui)
        self.set_logging_level()
        self.ui.itemsListParam.cellClicked.connect(self.on_itemsListParam_cellClicked)
        self.ui.itemsListParam.valChanged.connect(self.on_itemsListParam_valChanged)
        self.ui.configList.itemSelectionChanged.connect(self.ui.configList.clearSelection)
        self.ui.stop_condition.addItems(DataGenerator2D.DataGenerator2D.stop_conditions)
        self.ui.stop_condition.currentIndexChanged.connect(self.on_stop_condition_currentTexChanged)
        self.ui.logging_option.currentIndexChanged.connect(self.set_logging_level)

        self.lastOpenDirPath = os.path.abspath(os.path.expanduser("~"))
        self.target_dir = ""

        self.generator_name_to_inputs = {}  # DataGenerator2D.name: GenerateConfig
        self.data_generators = []

        self.image_galleries = {}
        self.attachment_galleries = {}


        self.ui.property_widget.set_properties(property_template_path, order_tooltip_path)
        self.items_with_order = gen_item_order_and_desc(order_tooltip_path)[0]
        self.init_settings_list()
        self.on_destPath_editingFinished()
        self.ui.stop_condition.currentIndexChanged.emit(self.ui.stop_condition.currentIndex())
        self.set_is_regression_test_status()

    @pyqtSlot()
    def set_logging_level(self):
        logging.getLogger().setLevel(self.ui.logging_option.currentIndex()*10)

    @pyqtSlot()
    def on_browse_seed_path_clicked(self):
        dir_path = self._open_dir()
        if not verify_file_path(dir_path):
            return
        self.ui.seedPath.setText(dir_path)
        self.select_load_dataset_mode()

    @pyqtSlot()
    def on_seedPath_editingFinished(self):
        dir_path = self.ui.seedPath.text()
        if not verify_file_path(dir_path):
            return
        self.load_seeds(seed_path=dir_path)

    @pyqtSlot()
    def on_browse_attach_path_clicked(self):
        dir_path = self._open_dir()
        if not verify_file_path(dir_path):
            return
        self.ui.attachment_path.setText(dir_path)
        self.load_attachments(attachment_path=dir_path)

    @pyqtSlot()
    def on_attachment_path_editingFinished(self):
        dir_path = self.ui.attachment_path.text()
        if not verify_file_path(dir_path):
            return
        self.load_attachments(attachment_path=dir_path)

    @pyqtSlot()
    def on_browse_target_dir_clicked(self):
        self.ui.destPath.setText(self._open_dir())
        self.target_dir = self.ui.destPath.text()

    @pyqtSlot()
    def on_destPath_editingFinished(self):
        self.target_dir = self.ui.destPath.text()

    @pyqtSlot()
    def on_actionSave_triggered(self):
        self.save_config()

    @pyqtSlot()
    def on_actionSave_As_triggered(self):
        self.save_config(self._open_dir())

    @pyqtSlot()
    def on_actionRegression_Test_triggered(self):
        print("clicked:", self.ui.actionRegression_Test.isChecked())
        img_process_util.is_regression_test = self.ui.actionRegression_Test.isChecked()

    @pyqtSlot(int)
    def on_generate_num_valueChanged(self, num):
        # self.ui.itemsListParam.show_column(self.ui.itemsListParam.column_count() - 1, bool(num == 0))
        current_data_generator = self.get_current_generator()
        if current_data_generator is not None:
            self.generator_name_to_inputs[
            current_data_generator.name].generate_image_num = self.ui.generate_num.value()

    @pyqtSlot()
    def on_stop_condition_currentTexChanged(self):
        if self.ui.stop_condition.currentText() == 'By Image Num':
            self.ui.itemsListParam.set_column_enable(self.ui.itemsListParam.column_count() - 1, isEnable=False)
            self.ui.generate_num.setEnabled(True)
        elif self.ui.stop_condition.currentText() == 'By Seed Num':
            self.ui.itemsListParam.set_column_enable(self.ui.itemsListParam.column_count() - 1, isEnable=True)
            self.ui.generate_num.setEnabled(False)
        self.generator_name_to_inputs[
            self.generator_selected().name].stop_condition = self.ui.stop_condition.currentText()

    @pyqtSlot()
    def on_createConfig_clicked(self):
        current_text, _ = QInputDialog.getText(self, "Config Name", "Please input config name:", QLineEdit.Normal,
                                               self.ui.configList.currentItem().text())
        if len(current_text) == 0:
            return
        current_text = self.update_config_name(current_text)
        self.create_data_generator(current_text)
        self.generator_name_to_inputs = self._update_generator_name_to_inputs(self.generator_name_to_inputs)
        self.update_item_status()

    @pyqtSlot()
    def on_loadConfig_clicked(self):
        config_path = self._open_dir()
        if os.path.exists(config_path) and os.path.isdir(config_path):
            config_json_file = os.path.join(config_path, 'config.json')
            if not verify_file_path(config_json_file, is_dir=False):
                return

            gen_json = util.read_json_config_file(os.path.join(config_path, 'config.json'))
            for key, gen_config in gen_json.items():
                if sorted(gen_config["generator"]["operator_types"]) != sorted(self.items_with_order):
                    raise ValueError("config loaded isn't consistant with order_tooltip.json!")
                gen_config["generator"]["operator_types"] = copy.deepcopy(self.items_with_order)
                self.load_data_generator(generator_json=gen_config['generator'], config_json=gen_config['input'])
                label_to_density_gennum_from_config_json = gen_config['input']['label_to_density_gennum']
                seed_path = gen_config['input']['seed_path']
                attachment_path = gen_config['input']['attachment_path']
                if os.path.exists(seed_path) and os.path.isdir(seed_path):
                    self.load_seeds(seed_path, label_to_density_gennum_from_config_json)
                    self.ui.seedPath.setText(seed_path)
                else:
                    self.ui.seedPath.setText("")
                if os.path.exists(attachment_path) and os.path.isdir(attachment_path):
                    self.load_attachments(attachment_path)
                    self.ui.attachment_path.setText(attachment_path)
                else:
                    self.ui.attachment_path.setText("")
            # {'default_1': <generate_data.GenerateConfig.GenerateConfig object at 0x7fda3805ae10>, 'default':
        self.on_stop_condition_currentTexChanged()
    # todo: will add context menu for delete action
    @pyqtSlot()
    def on_clear_attach_list_clicked(self):
        attachment_gallery = self.attachment_galleries[self.get_current_generator().name]
        attachment_gallery.clear()
        for config in self.generator_name_to_inputs.values():
            for item_label in config.label_to_attachment_list.keys():
                config.label_to_attachment_list[item_label] = {}
        self.update_item_status()

    @pyqtSlot()
    def on_clear_seed_list_clicked(self):
        image_gallery = self.image_galleries[self.get_current_generator().name]
        image_gallery.clear_selected(self.get_selected_current_dict_key())
        current_config_name = self.get_current_generator().name
        config = self.generator_name_to_inputs[current_config_name]
        for i in self.ui.itemsListParam.selected_current_dict_key:
            del config.label_to_density_gennum[i]
        config.label_to_items = image_gallery.label_to_items
        config.label_to_attachment_list = {}
        item = self.ui.configList.currentItem()
        if item is not None:
            self.ui.configList.itemActivated.emit(item)
        else:
            current_data_generator = self.get_current_generator()
            self.ui.itemsListParam.bind_multi_dict_to_widget(
                self.generator_name_to_inputs[current_data_generator.name].label_to_density_gennum,
                GenerateConfig.density_gennum_params)
        self.clear_cell_selections_from_ui_itemsListParam()
        self.update_item_status()

    @pyqtSlot(QListWidgetItem)
    def on_configList_itemActivated(self, item):
        logging.info("config: " + item.text() + " activated")
        self.ui.configList.setCurrentItem(item)
        generator_name = self.ui.configList.currentItem().text()
        logging.info("configlist itemActivated " + generator_name)
        generator_selected = self.find_data_generator(generator_name)
        if generator_selected is None:
            return
        operator_types, operator_type_to_param = generator_selected.get_operator_types_and_params()
        self.ui.property_widget.bind_dict(operator_types, operator_type_to_param)
        self.ui.itemsListParam.bind_multi_dict_to_widget(
            self.generator_name_to_inputs[self.generator_selected().name].label_to_density_gennum,
            sub_dict_keys=GenerateConfig.density_gennum_params)
        self.ui.generate_num.setValue(self.generator_name_to_inputs[self.generator_selected().name].generate_image_num)
        self.ui.stop_condition.setCurrentText(
            self.generator_name_to_inputs[self.generator_selected().name].stop_condition)
        self.ui.seedPath.setText(self.generator_name_to_inputs[self.generator_selected().name].seed_path)
        self.ui.attachment_path.setText(self.generator_name_to_inputs[self.generator_selected().name].attachment_path)
        self.update_item_status()
        self.on_stop_condition_currentTexChanged()

    @pyqtSlot()
    def on_delConfig_clicked(self):
        if self.ui.configList.count() <= 1:
            return
        item = self.ui.configList.currentItem()
        logging.info('del ' + item.text())
        if item is None:
            return
        row = self.ui.configList.row(item)
        to_delete_item = self.ui.configList.takeItem(row)
        del to_delete_item
        for idx in range(len(self.data_generators)):
            if self.data_generators[idx].name == item.text():
                break
        self.data_generators.pop(idx)
        self.ui.configList.setCurrentRow(self.ui.configList.count() - 1)
        try:
            self.generator_name_to_inputs.pop(item.text())
        except ValueError:
            logging.info('config no seed path')

    @pyqtSlot(str)
    def on_itemsListParam_cellClicked(self, item_label):
        logging.info(item_label)
        if item_label in self.generator_name_to_inputs[
            self.get_current_generator().name].label_to_attachment_list.keys():
            self.ui.attachmentList.bind_multi_dict_to_widget(
                dic=self.generator_name_to_inputs[self.get_current_generator().name].label_to_attachment_list[
                    item_label],
                sub_dict_keys=GenerateConfig.attachment_params)

    @pyqtSlot()
    def on_randomGenerate_clicked(self): 
        if not self.check_background():
            QMessageBox.information(self, 'info', "you should select and only select one background among file_bg,random_noise_bg and color_bg in every config")
            return
        generate_helper.generate_parallel(dest_path=self.target_dir, prefix='2007_',
                                          generator_name_to_inputs=self.generator_name_to_inputs,
                                          data_generators=self.data_generators,
                                          is_singleprocessing=self.ui.actionSingle_Process.isChecked())
        expected_image_num = util.get_expected_image_num(configs=self.generator_name_to_inputs)
        is_equal, actual_image_num = util.check_image_num(dir_path=self.target_dir, generate_image_num=expected_image_num)
        if not is_equal:
            QMessageBox.information(self, 'info', "The number of images does not match the expected value, expect:"+str(expected_image_num)+',actual:'+str(actual_image_num))
        label_to_num = voc_data_checker.get_label_info(self.target_dir)
        QMessageBox.information(self, 'info', str(label_to_num))

    @pyqtSlot()
    def on_preview_clicked(self):
        if img_process_util.is_regression_test:
            np.random.seed(5)
        _config = copy.deepcopy(self.generator_name_to_inputs[self.get_current_generator().name])
        _image, _ = DataGenerator2D.generate_one_image(data_generator=self.get_current_generator(), config=_config)
        cv2.imshow('Preview', _image)
        cv2.waitKey(0)
        cv2.destroyWindow('Preview')

    # todo
    @pyqtSlot()
    def on_randomGenerate_train_clicked(self):
        if self._check_generate_config_saved():
            dest_path = os.path.abspath(os.path.expanduser(self.target_dir))
            train_test_ratio = self.ui.train_test_ratio.value() / 100
            train_val_ratio = self.ui.train_val_ratio.value() / 100
            pos_neg_ratio = self.ui.pos_neg_ratio.value() / 100

        else:
            QMessageBox.information(
                self, "Info", "The current config has not been saved",
                QMessageBox.Ok)

    '''
    self defined function, not slot
    '''
    def get_selected_current_dict_key(self):
        return self.ui.itemsListParam.selected_current_dict_key

    def clear_cell_selections_from_ui_itemsListParam(self):
        self.ui.itemsListParam.clear_cell_selections()

    def get_current_generator(self):
        if self.ui.configList.currentItem() is None:
            return None
        text = self.ui.configList.currentItem().text()
        return self.find_data_generator(text)

    def init_settings_list(self):
        self.data_generators.clear()
        default_settings = gen_default_settings_with_type(gen_properties_template(property_template_path))
        generator_json = {
            "name":"config",
            "operator_types":self.items_with_order,
            "operator_type_to_param":default_settings,
            "project_path":""}
        self.load_data_generator(generator_json, default_settings)
        self._update_generator_name_to_inputs(self.generator_name_to_inputs)

    def create_data_generator(self, name):
        current_data_generator = self.get_current_generator()
        operator_types, operator_type_to_param = current_data_generator.get_operator_types_and_params()
        new_data_generator = DataGenerator2D.DataGenerator2D(name=name, operator_types=operator_types,
                                                             operator_type_to_params=operator_type_to_param)

        self.generator_name_to_inputs[new_data_generator.name] = GenerateConfig(
            generate_image_num=self.ui.generate_num.value())

        self.create_image_attachment_gallery(new_data_generator.name)
        image_gallery = self.image_galleries[new_data_generator.name]
        attachment_gallery = self.attachment_galleries[new_data_generator.name]

        # use global label to items and label to desity gennum
        self.generator_name_to_inputs[new_data_generator.name].generate_image_num = self.ui.generate_num.value()
        self.generator_name_to_inputs[new_data_generator.name].stop_condition = self.ui.stop_condition.currentText()
        self.generator_name_to_inputs[new_data_generator.name].label_to_items = image_gallery.label_to_items
        self.generator_name_to_inputs[
            new_data_generator.name].label_to_attachment = attachment_gallery.label_to_items

        self.generator_name_to_inputs[new_data_generator.name].label_to_density_gennum = \
            copy.deepcopy(self.generator_name_to_inputs[current_data_generator.name].label_to_density_gennum)
        self.data_generators.append(copy.deepcopy(new_data_generator))  # add generator

        self.bind_widgets_to_generator(
            self.find_data_generator(new_data_generator.name))  # bind object list and algo list widget
        self.ui.configList.addItem(new_data_generator.name)
        self.ui.configList.setCurrentRow(self.ui.configList.count() - 1)

    def create_image_attachment_gallery(self, generate_name):
        self.image_galleries[generate_name] = ImageGallery()
        self.attachment_galleries[generate_name] = ImageGallery()

    def load_data_generator(self, generator_json, config_json):
        new_data_generator = DataGenerator2D.DataGenerator2D()
        new_data_generator.from_json(generator_json)
        if self.check_if_config_exist(new_data_generator.name):
            if QMessageBox.Cancel == QMessageBox.question(self, "Question",
                                                          "Config name exist, still load and rename? ",
                                                          QMessageBox.Yes | QMessageBox.Cancel):
                return
            else:
                new_data_generator.name = self.update_config_name(new_data_generator.name)

        if config_json is None:
            self.generator_name_to_inputs[new_data_generator.name] = GenerateConfig()
        elif not 'generate_image_num' in config_json:
            self.generator_name_to_inputs[new_data_generator.name] = GenerateConfig(generate_image_num=self.ui.generate_num.value())
        else:
            self.generator_name_to_inputs[new_data_generator.name] = GenerateConfig(config_json)

        self.data_generators.append(copy.deepcopy(new_data_generator))  # add generator

        self.create_image_attachment_gallery(new_data_generator.name)

        self.bind_widgets_to_generator(
            self.find_data_generator(new_data_generator.name))  # bind object list and algo list widget
        self.ui.configList.addItem(new_data_generator.name)
        self.ui.configList.setCurrentRow(self.ui.configList.count() - 1)

    def find_data_generator(self, name):
        for generator in self.data_generators:
            if generator.name == name:
                return generator
        return None

    def bind_widgets_to_generator(self, generator):
        operator_types, operator_type_to_param = generator.get_operator_types_and_params()
        logging.info("bind widget to generator:" + str(operator_types))
        self.ui.property_widget.bind_dict(key_orders=operator_types, dic=operator_type_to_param)
        self.ui.itemsListParam.bind_multi_dict_to_widget(
            self.generator_name_to_inputs[generator.name].label_to_density_gennum,
            GenerateConfig.density_gennum_params)


    def update_config_name(self, name):
        config_name_split = name.split('_')[0]
        n = 0
        while name in [self.ui.configList.item(i).text() for i in range(self.ui.configList.count())]:
            name = config_name_split + '_' + str(self.ui.configList.count() + n)
            n += 1
        return name

    def update_item_status(self):
        image_gallery = self.image_galleries[self.get_current_generator().name]
        seed_status = "Seed Unloaded" if len(image_gallery.label_to_items) == 0 else "Seed Loaded"
        self.ui.seed_status.setStyleSheet(
            STATUS_STYLE_WARNING if len(image_gallery.label_to_items) == 0 else STATUS_STYLE_OK)
        self.ui.seed_status.setText(seed_status)

        attachment_gallery = self.attachment_galleries[self.get_current_generator().name]

        attach_status = "Attachment Unloaded" if len(
            attachment_gallery.label_to_items) == 0 else "Attachment Loaded"
        self.ui.attach_status.setStyleSheet(
            STATUS_STYLE_WARNING if len(attachment_gallery.label_to_items) == 0 else STATUS_STYLE_OK)
        self.ui.attach_status.setText(attach_status)

    def check_if_config_exist(self, name):
        return any(self.ui.configList.item(i).text() == name for i in range(self.ui.configList.count()))
    
    def check_background(self):
        return all([DataGenerator2D.check_backgorund_in_generator(generator) for generator in self.data_generators])

    def _update_generator_name_to_inputs(self, generator_name_to_inputs={}, seed_path="", attachment_path="", label_to_density_gennum_from_config_json={}):
        current_config_name = self.get_current_generator().name
        label_to_items = self.image_galleries[current_config_name].label_to_items
        label_to_attachment = self.attachment_galleries[current_config_name].label_to_items
        config = generator_name_to_inputs[current_config_name]
        config.seed_path = seed_path
        config.attachment_path = attachment_path

        config.label_to_items = label_to_items
        config.label_to_density_gennum = config.update_label_to_density_gennum(label_to_items=label_to_items, label_to_density_gennum_from_config_json=label_to_density_gennum_from_config_json)
        config.label_to_attachment = label_to_attachment
        config.label_to_attachment_list = config.update_label_to_attachment_list(
            label_to_items=config.label_to_items,
            label_to_attachment=label_to_attachment,
            label_to_attachment_list=config.label_to_attachment_list)
        generator_name_to_inputs[current_config_name] = config

        return generator_name_to_inputs

    def load_seeds(self, seed_path='', label_to_density_gennum_from_config_json={}):
        image_gallery = self.image_galleries[self.get_current_generator().name]
        _ = image_gallery.load_multi_items(objects_path=seed_path)

        attachment_path = self.ui.attachment_path.text()

        self.generator_name_to_inputs = self._update_generator_name_to_inputs(self.generator_name_to_inputs, seed_path, attachment_path=attachment_path, label_to_density_gennum_from_config_json=label_to_density_gennum_from_config_json)

        current_data_generator = self.get_current_generator()
        self.ui.itemsListParam.bind_multi_dict_to_widget(
            self.generator_name_to_inputs[current_data_generator.name].label_to_density_gennum,
            GenerateConfig.density_gennum_params)
        self.ui.stop_condition.currentIndexChanged.emit(self.ui.stop_condition.currentIndex())
        self.update_item_status()

    def load_attachments(self, attachment_path=''):
        attachment_gallery = self.attachment_galleries[self.get_current_generator().name]
        _ = attachment_gallery.load_attachments(objects_path=attachment_path)
        seed_path = self.ui.seedPath.text()
        self.generator_name_to_inputs = self._update_generator_name_to_inputs(self.generator_name_to_inputs, seed_path=seed_path, attachment_path=attachment_path)
        self.update_item_status()

    def save_config(self, dir_path=None):
        if dir_path is None:
            target_dir = self.target_dir
        else:
            target_dir = dir_path
        if not verify_file_path(target_dir):
            return

        self._save_generation_param(target_dir)
        QMessageBox.information(self, "Info", "Saved config to: " + target_dir)

    def on_itemsListParam_valChanged(self):
        pass  # todo

    def _save_generation_param(self, config_path):
        gen_param = {}
        for data_generator in self.data_generators:
            gen_param[data_generator.name] = {'generator': data_generator.to_json(),
                                              'input': self.generator_name_to_inputs[data_generator.name].__dict__}

        with open(os.path.join(config_path, 'config.json'), 'w') as fout:
            fout.write(json.dumps(gen_param, indent=4, cls=ExtendJSONEncoder))

    def _check_generate_config_saved(self):
        current_config = self._read_generate_config()
        current_cfg_saved = False
        for cfg_name, cfg in self.ocConfigs.items():
            if cfg.__dict__ == current_config.__dict__:
                current_cfg_saved = True
                break
        return current_cfg_saved

    def _open_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Open Directory', self.lastOpenDirPath,
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)

        self.lastOpenDirPath = dir_path
        return dir_path

    def closeEvent(self, *args, **kwargs):
        settings.write_settings("setting.ini", self.ui.__dict__)

    def generator_selected(self):
        generator_name = self.ui.configList.currentItem().text()
        generator_selected = self.find_data_generator(generator_name)
        if generator_selected is None:
            return
        return generator_selected

    def set_is_regression_test_status(self):
        print("set:", self.ui.actionRegression_Test.isChecked())
        img_process_util.is_regression_test = self.ui.actionRegression_Test.isChecked()

    def select_load_dataset_mode(self):
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle('load seed')
        box.setText("Please Select the way to load the seed, "
                    "you can load in new config or load in current config (will overwrite current seeds)!")
        box.setStandardButtons(QMessageBox.Ok | QMessageBox.No | QMessageBox.Cancel)
        creat_config = box.button(QMessageBox.Ok)
        creat_config.setText('New')
        replace_config = box.button(QMessageBox.No)
        replace_config.setText('Replace')
        box.exec_()
        if box.clickedButton() == creat_config:
            self.on_createConfig_clicked()
            self.load_seeds(seed_path=self.ui.seedPath.text())
        elif box.clickedButton() == replace_config:
            self.load_seeds(seed_path=self.ui.seedPath.text())
        else:
            self.ui.seedPath.setText('')
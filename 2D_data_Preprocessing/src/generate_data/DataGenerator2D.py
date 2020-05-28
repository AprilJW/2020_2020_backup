import os
import sys
import copy
import time
import numpy as np
import cv2
import tqdm
import traceback

from util import img_process_util, util
from generate_data.GenerateConfig import GenerateConfig
from cutout.ImageGallery import ImageGallery
from generate_data import operator_factory


sys.path.append(os.path.abspath(os.path.expanduser('../../dataset_tools/src')))
from libs.json_io.json_parser_io import JsonParserIO
from libs.json_io.json_parser_io import ObjectDescInfo
from libs.dir_and_filename_info import *
from libs.json_io import json_parser_io
import logging

# np.random.seed(np.int64(time.time()))


class DataGenerator2D:
    """
        blend 2d images

        Attribute:
    """
    inputs = {'label_to_items', 'label_to_density_gennum', 'label_to_attachments', 'label_to_attachment_param', "seed_path", "attachment_path"}
    stop_conditions = ['By Image Num', 'By Seed Num']

    def __init__(self, data=None, name='', operator_types=[], operator_type_to_params={}):
        if data:
            self.__dict__.updata(data)
        else:
            self.name = name
            self.project_path = ''
        self.operators = self._create_operators(operator_types=operator_types,
                                                operator_type_to_params=operator_type_to_params)

    """ roi is [xmin,ymin,xmax,ymax]"""

    def _create_operators(self, operator_types=[], operator_type_to_params={}):
        _operators = []
        if len(operator_types) > 0:
            for operator_name in operator_types:
                if operator_name in operator_type_to_params.keys():
                    _operators.append(operator_factory.create_operator(parent_generator=self, operator_type=operator_name,
                                                         operator_param=operator_type_to_params[operator_name]))
                else:
                    _operators.append(
                        operator_factory.create_operator(parent_generator=self, operator_type=operator_name,
                                                         operator_param={}))
        else:
            _operator_type_to_operator = operator_factory.get_all_operator()
            for operator_types, operator_cls in _operator_type_to_operator.items():
                _operators.append(operator_cls())
        return _operators

    def get_operator_types_and_params(self):
        operator_types = [operator.type for operator in self.operators]
        operator_type_to_param = {operator.type: operator.__dict__ for operator in
                                  self.operators}
        return operator_types, operator_type_to_param

    def to_json(self):
        json_dict = copy.deepcopy(self.__dict__)
        json_dict['operator_types'] = [operator.type for operator in self.operators]
        json_dict['operator_type_to_param'] = {operator.type: operator.__dict__ for operator in self.operators}
        json_dict.pop('operators', None)
        return json_dict

    def from_json(self, param_json=None):
        if param_json:
            _operators = self._create_operators(operator_types=param_json['operator_types'],
                                                operator_type_to_params=param_json['operator_type_to_param'])
            param_json.pop('operator_types', None)
            param_json.pop('operator_type_to_param', None)
            param_json['operators'] = _operators
            self.__dict__ = param_json

    def count_item_num(self):
        ret = {}
        for item in self.items:
            if not item.is_covered:
                if item.name not in ret.keys():
                    ret[item.name] = 1
                else:
                    ret[item.name] += 1
        return ret

    def process(self, config=GenerateConfig()):
        try:
            keys = []
            for key in config.label_to_density_gennum.keys():  # exmple {'TULING': {'GenNum': 1.0, 'SeedNum': 22, 'DensityMax': 2, 'DensityMin': 0}}
                if config.label_to_density_gennum[key]["DensityMax"] == 0:
                    keys.append(key)
            for key in keys:
                config.label_to_density_gennum.pop(key, None)
            _key_to_inputs = config.__dict__
            _key_to_outputs = {}
            for operator in self.operators:  # all algorithm
                if operator.is_used:
                    logging.info(operator.type)
                    outputs = operator.process(_key_to_inputs)
                    print(operator.type, 'finished')
                    for output_key, output in zip(operator.outputs, outputs):
                        _key_to_outputs[output_key] = output
                    _key_to_inputs = _key_to_outputs
            return _key_to_outputs
        except Exception:
            traceback.print_exc()

def check_backgorund_in_generator(data_generator=DataGenerator2D()):
    bgs = ["file_bg", "color_bg", "random_noise_bg"]
    count = 0
    for operator in data_generator.operators:
        if operator.type in bgs and operator.is_used:
            count += 1
    return count == 1

def _get_operator_by_name(operator_name='', operator_param={}):
    return operator_factory.create_operator(operator_name, operator_param)


def _write_color_img(img=[], idx=0, dest_path='', prefix='2007_'):
    file_name = util.get_str_file_name(idx=idx, prefix=prefix, surfix='.jpg')
    img_full = os.path.join(dest_path, 'images', file_name)
    cv2.imwrite(img_full, img)


def _items_to_object_annotations(items=[]):
    objects = []
    for item in items:
        if item.is_covered:
            continue
        if type(item.maskContour) is dict:
            contours = [cnt.tolist() for cnt in item.maskContour['contours']]
            hierarchy = item.maskContour['hierarchy'].tolist()
        elif type(item.maskContour) is not list:
            contours = [item.maskContour.tolist()]
            hierarchy = [[[-1, -1, -1, -1]]]
        else:
            contours = item.maskContour
            hierarchy = [[[-1, -1, -1, -1]]]
        obj_anno = ObjectDescInfo()
        obj_anno.label = item.name
        obj_anno.is_covered = item.is_covered
        obj_anno.difficult = item.difficult
        obj_anno.keypoints = item.keypoints
        obj_anno.bndbox = [item.bndbox[0], item.bndbox[1], item.bndbox[2] - item.bndbox[0],
                           item.bndbox[3] - item.bndbox[1]]
        obj_anno.rot_box = item.rot_box
        obj_anno.contours = contours
        obj_anno.hierarchy = hierarchy
        objects.append(obj_anno)
    return objects


def _write_json(idx=0, dest_path='', prefix='2007_', items=[], generate_image_shape=[]):
    file_name = util.get_str_file_name(idx=idx, prefix=prefix, surfix='.json')
    json_full = os.path.join(dest_path, DIR_LABELS, file_name)
    mask_anno = JsonParserIO()
    objects = []
    for item in items:
        if item.is_contain_sub_items():
            try:
                objects += (_items_to_object_annotations(item.sub_items))
            except:
                logging.info('items_to_object_annotations'+  sys.exc_info())
        else:
            try:
                objects += (_items_to_object_annotations([item]))
            except:
                logging.info('items_to_object_annotations'+ sys.exc_info())
    mask_anno.image_shape = generate_image_shape
    mask_anno.objects = objects
    json_parser_io.write_json(mask_anno, json_full)


def generate_one_image(data_generator=DataGenerator2D(), config=GenerateConfig()):
    _key_to_outputs = data_generator.process(config)
    b, g, r, _ = cv2.split(_key_to_outputs['image'])
    img = cv2.merge([b, g, r])
    return img, _key_to_outputs


def update_seed_num(_label_to_item_count, label_to_density_gennum):
    _label_to_density_gennum = copy.deepcopy(label_to_density_gennum)
    for label, count in _label_to_item_count.items():
        if label in _label_to_density_gennum.keys():
            _label_to_density_gennum[label]['GenNum'] -= count
            if _label_to_density_gennum[label]['GenNum'] <= 0:
                _label_to_density_gennum.pop(label, None)
        print(_label_to_density_gennum)
    return _label_to_density_gennum


def _remain_generate_image_num(image_num=0, required_image_num=0):
    return required_image_num - image_num

def _remain_generate_seed_num(label_to_density_gennum={}):
    return sum([label_to_density_gennum[key]['GenNum'] for key in label_to_density_gennum.keys()])

def generate_executor(dest_path='', prefix='2007_', config_key='', data_generator=DataGenerator2D(),
                      config=GenerateConfig()):
    # np.random.seed(np.int64(time.time() + int(config_key)))
    _config = copy.deepcopy(config)
    _image_num = 0
    _remain_num = 0
    if _config.stop_condition == 'By Image Num':
        print('process', config_key, 'required_image_num', _config.generate_image_num)
        _remain_num = _remain_generate_image_num(image_num=_image_num,
                                                 required_image_num=_config.generate_image_num)
    elif _config.stop_condition == 'By Seed Num':
        _remain_num = _remain_generate_seed_num(label_to_density_gennum=_config.label_to_density_gennum)
    while _remain_num > 0:

        print('process', config_key, '_remain_num', _remain_num)
        img, _key_to_outputs = generate_one_image(data_generator=data_generator, config=_config)
        _write_color_img(img, idx=_image_num, dest_path=dest_path, prefix=prefix)
        _write_json(items=_key_to_outputs['items'], idx=_image_num, dest_path=dest_path, prefix=prefix,
                    generate_image_shape=list(img.shape))
        _image_num += 1

        if _config.stop_condition == 'By Image Num':
            _remain_num = _remain_generate_image_num(image_num=_image_num,
                                                     required_image_num=_config.generate_image_num)
        elif _config.stop_condition == 'By Seed Num':
            _label_to_item_count = _key_to_outputs['_label_to_item_count']
            _config.label_to_density_gennum = update_seed_num(_label_to_item_count=_label_to_item_count,
                            label_to_density_gennum=_config.label_to_density_gennum)
            _remain_num = _remain_generate_seed_num(label_to_density_gennum=_config.label_to_density_gennum)


if __name__ == '__main__':
    src = 'D:/data/distort'
    test = ImageGallery()
    test.load_multi_items(src)
    config = GenerateConfig()
    config.label_to_items = test.label_to_items
    config.label_to_density_gennum = {'distort': {'DensityMin': 1, 'DensityMax': 5, 'GenNum': 30}}

    config.operator_names = ['SeedItemPicker', 'RandomHighLight', 'ItemBlender', 'color_bg', 'ItemsToImage',
                             'UpdateGenerateNum']
    config.operator_to_params = {
        'SeedItemPicker': {'label_to_density_gennum': config.label_to_density_gennum, 'is_norm_distribution': False},
        # 'Brightness': {'brightness_lower': -50, 'brightness_upper': 50, 'scale': 1},
        # 'Contrast': {'clip_limit': 4.0, 'tile_grid_size' : (8, 8)},
        # 'HueTune': {'target_hue': 0.1},
        # 'Move': {'image_shape' : (500, 500), 'pos_x' : 10, 'pos_y' : 10},
        # 'RandomHighLight': {'min_hl_num': 0, 'max_hl_num': 10, 'min_hl_area': 100, 'max_hl_area': 1000},  # todo
        # 'Resize':{'resize_width_lower':1.0, 'resize_width_upper':1.0, 'resize_height_lower':1.0, 'resize_height_upper':1.0, "is_same_size_in_image":True, "is_same_size_in_class":False},
        # 'Rotation':{'angle_lower':0.0, 'angle_upper':360.0},
        # 'Shadow':{'shade_offset':-30, 'shade_scale':1},
        # 'Distortion':{'grid_width':4, 'grid_height':4, 'magnitude':4},
        'ItemBlender': {'image_width': 1292, 'image_height': 964, 'is_sharp_edge': False, 'exposed_area': 0.7},
        'color_bg': {'r': 100, 'g': 0, 'b': 0, 'image_height': 964, 'image_width': 1292},
        'ItemsToImage': {},
        'UpdateGenerateNum': {}}
    oc = DataGenerator2D(operator_types=config.operator_names, operator_type_to_params=config.operator_to_params)
    generate_executor(dest_path='D:/data/distort', config_key='1', data_generator=oc, config=config)
    print(config._get_all_operator_param_dicts())
    pass

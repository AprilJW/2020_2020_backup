import os, sys
import math
import copy
import multiprocessing as mp
import time
import logging
import numpy as np
import traceback

import matplotlib

matplotlib.use('Agg')

sys.path.append(os.path.abspath(os.path.expanduser('../../dataset_tools/src')))
sys.path.append(os.path.abspath(os.path.expanduser('../../../dataset_tools/src')))
from libs.dir_and_filename_info import *
from generate_data import ItemIntegrator
from libs import voc_data_checker
from generate_data import DataGenerator2D
from util import img_process_util

datagenerator2d_debug_status = False


def _separate_task_config(config, size=1):
    configs = []
    _config = copy.deepcopy(config)
    print('stop_condition', _config.stop_condition)
    print('size', size)
    if size == 0:
        return []
    if _config.stop_condition == 'By Image Num':
        if _config.generate_image_num < size:
            size = _config.generate_image_num
        _config.generate_image_num = int(_config.generate_image_num / size)

    else:
        for key in _config.label_to_density_gennum.keys():
            _config.label_to_density_gennum[key]['GenNum'] /= size

    for i in range(size):
        configs.append(copy.deepcopy(_config))

    left_over_gennum = config.generate_image_num - size * _config.generate_image_num
    if left_over_gennum > 0:
        configs[0].generate_image_num += left_over_gennum

    return configs


def _generate(dest_path="", prefix='2007_', config_key='', config=None, oc=None, seed=None, is_regression_test=False):
    try:
        img_process_util.is_regression_test = is_regression_test
        if img_process_util.is_regression_test:
            np.random.seed(seed)
        else:
            np.random.seed(np.int64(time.time() + int(config_key)))
        make_data_dirs(dest_path=dest_path)  # dataset_tools.libs.dir_and_filename_info
        DataGenerator2D.generate_executor(dest_path=dest_path, prefix=prefix, config_key=config_key, data_generator=oc,
                                          config=config)
    except Exception:
        raise Exception("".join(traceback.format_exception(*sys.exc_info())))


def generate_parallel(dest_path="", prefix='2007_', generator_name_to_inputs={}, data_generators=[],
                      is_singleprocessing=False):
    try:       
        start = time.time()
        for data_generator in data_generators:
            pool = mp.Pool(processes=int(mp.cpu_count() / 2) + 1)
            sub_configs = _separate_task_config(config=generator_name_to_inputs[data_generator.name],
                                                size=int(mp.cpu_count() / 2) + 1)
            print('sub_configs: ', sub_configs)
            print('cpu_count: ', mp.cpu_count(), "is_singleprocessing: ", is_singleprocessing)
    
            if is_singleprocessing:
                for i in range(len(sub_configs)):
                    _generate(dest_path=os.path.join(dest_path, data_generator.name, str(i)), prefix=prefix,
                              config_key=str(0),
                              config=sub_configs[i],
                              oc=data_generator)
            else:
                np.random.seed(5)
                seed_list = [np.random.randint(0, 100) for i in range(int(mp.cpu_count() / 2) + 1)]
                results = [pool.apply_async(_generate, (
                    os.path.join(dest_path, data_generator.name, str(i)), prefix, str(i), sub_configs[i],
                    data_generator, seed_list[i], img_process_util.is_regression_test))
                 for i in range(len(sub_configs))]
    
            pool.close()
            pool.join()
        [print(item.get()) for item in results]  
    except Exception:
        traceback.print_exc()    

    for _data_generator in data_generators:
        merge_src_paths = []
        src_paths = os.listdir(os.path.join(dest_path, _data_generator.name))
        src_paths = [os.path.join(dest_path, _data_generator.name, sub_path) for sub_path in src_paths]
        merge_src_paths.extend(src_paths)
        voc_data_checker.merge_data_set(src_paths=merge_src_paths, dest_path=dest_path)

    for _data_generator in data_generators:
        shutil.rmtree(os.path.join(dest_path, _data_generator.name))
    logging.info(str(time.time() - start))
    

def _get_low_density_expectation(items=[], target_roi_wh=[], resize_ratio_w=[], resize_ratio_h=[]):
    item_width_max = max(item.image.shape[0] for item in items)
    item_height_max = max(item.image.shape[1] for item in items)
    return math.ceil((target_roi_wh[0] / (item_width_max * (resize_ratio_w[1] + resize_ratio_w[0]) / 2)) * (
            target_roi_wh[1] / (item_height_max * (resize_ratio_h[1] + resize_ratio_h[0]) / 2)))


def _get_high_density_expectation(items=[], target_roi_wh=[], resize_ratio_w=[], resize_ratio_h=[]):
    item_width_min = min(item.image.shape[0] for item in items)
    item_height_min = min(item.image.shape[1] for item in items)
    return math.ceil((target_roi_wh[0] / (item_width_min * (resize_ratio_w[0] + resize_ratio_w[1]) / 2)) * (
            target_roi_wh[1] / (item_height_min * (resize_ratio_h[0] + resize_ratio_h[1]) / 2)))


def get_default_generate_configs(config=DataGenerator2D.GenerateConfig(), label_to_items={}):
    for key in label_to_items.keys():
        high_density = _get_high_density_expectation(label_to_items[key], config.target_roi_wh,
                                                     config.resize_radio_w_range, config.resize_radio_h_range)
        low_density = _get_low_density_expectation(label_to_items[key], config.target_roi_wh,
                                                   config.resize_radio_w_range, config.resize_radio_h_range)
        logging.info("key: "+ str(high_density)+ str(low_density))
        _config = DataGenerator2D.GenerateConfig()
        _config = copy.deepcopy(config)
    pass


if __name__ == '__main__':
    # generate_parallel("d:/", ['k1', 'k2', 'k3'])
    print(ItemIntegrator.operator_type_to_operator['ItemBlender'].__subclasses__())

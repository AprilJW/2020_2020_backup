import os
import datetime
import logging
from tqdm import tqdm
import cv2

from libs.dir_and_filename_info import *
from libs.dataset_format.dataset_utilities import dataset_util


class DatasetFormatter(object):
    """
    This class is a template for any dataset formatter under this module
    The input of a dataset formatter is a HUB Dataset
    The output of a dataset formatter is specified by child formatter, e.g.
    it can be a VOC dataset
    """
    def __init__(self, base_config=None):
        if base_config is not None:
            self.__dict__ = base_config
        else:
            self.paths = {DIR_IMAGES: '', DIR_DEPTH: '', DIR_LABELS: '', 'output': ''}
            self.debug_status = False
            self.split_ids = {'train': 0, 'minival': 0, 'val': 0}
            self.background_color = [0, 0, 0]
            self.separation_linewidth = 3
            self.generate_hierarchy_json = False
            self.unify_categories = False

    def set_default_config(self, src_path):
        self.paths[DIR_IMAGES] = os.path.join(src_path, DIR_IMAGES)
        self.paths[DIR_LABELS] = os.path.join(src_path, DIR_LABELS)
        self.paths[DIR_DEPTH] = os.path.join(src_path, DIR_DEPTH)
        self.paths['output'] = os.path.join(src_path, 'dataset_output')
        
    def get_root_path(self):
        suffix = str(datetime.datetime.now().date()).replace("-", "")
        return os.path.join(self.paths['output'], self.dataset_name+"_" + suffix)

    def get_debug_path(self):
        return os.path.join(self.get_root_path(), 'debug')

    def get_src_image_path(self):
        return self.paths[DIR_IMAGES]

    def get_src_depth_path(self):
        return self.paths[DIR_DEPTH]

    def get_src_label_filepath(self, img_id):
        return os.path.join(self.paths[DIR_LABELS], '2007_%06i.json' % (img_id))

    def get_dest_mode_path(self, mode, suffix=''):
        return os.path.join(self.get_root_path(), mode+suffix)

    def get_dest_mode_filename(self, mode, img_id, suffix='.jpg'):
        pass

    def get_image_size(self):
        w = int(self.image_size['width'])
        h = int(self.image_size['height'])
        return w, h

    def get_image_intervals(self, image_list):
        pass

    def get_split_intervals(self, image_list):
        pass

    def get_label_intervals(self, image_list):
        pass

    def build_dirs(self):
        logging.info('build directories...')
        dataset_util.create_workspace_dirs(self.get_root_path(), self.sub_dirs)
        if os.path.exists(self.get_src_depth_path()):
            for mode in self.image_modes:
                os.makedirs(self.get_dest_mode_path(mode, '_depth'))
        if self.debug_status:
            os.makedirs(self.get_debug_path())

    def _copy_images_per_mode(self, src_path, images_sublist, mode, dest_path):
        for srcfile in tqdm(images_sublist):
            img_id = dataset_util.get_image_id(srcfile)
            img_in = cv2.imread(os.path.join(src_path, srcfile))
            if img_in is None:
                print('Failed to read image file', srcfile)
                continue
            new_name = self.get_dest_mode_filename(mode, img_id)
            area = dataset_util.get_area(img_in.shape, *self.get_image_size())
            dataset_util.copy_image(area, img_in, os.path.join(dest_path, new_name),
                                    self.background_color)

    def _copy_depth_per_mode(self, src_path, images_sublist, mode, dest_path):
        for srcfile in tqdm(images_sublist):
            img_id = dataset_util.get_image_id(srcfile)
            depth_srcfile = dataset_util.get_same_name_file(src_path, srcfile)
            img_in = cv2.imread(os.path.join(src_path, depth_srcfile), cv2.IMREAD_UNCHANGED)
            if img_in is None:
                print('Failed to read depth file', srcfile)
                continue
            new_name = self.get_dest_mode_filename(mode, img_id,
                                                   suffix=os.path.splitext(depth_srcfile)[1])
            area = dataset_util.get_area(img_in.shape, *self.get_image_size())
            dataset_util.copy_image(area, img_in, os.path.join(dest_path, new_name),
                                    self.background_color)
            
    def copy_images(self, image_list, intervals):
        logging.info('copying images...')
        for mode in self.image_modes:
            dest_path = self.get_dest_mode_path(mode)
            images_sublist = image_list[intervals[mode][0]:intervals[mode][1]]
            self._copy_images_per_mode(self.get_src_image_path(), images_sublist, mode, dest_path)
            if os.path.exists(self.get_src_depth_path()):
                self._copy_depth_per_mode(self.get_src_depth_path(),
                                           images_sublist,
                                           mode,
                                           self.get_dest_mode_path(mode, '_depth'))

    def write_file_list(self, image_list, split_intervals):
        pass

    def generate_labels(self, image_list, label_intervals):
        pass

    def start_format(self):
        print('====START formatting %s====' % self.FORMATTER_TYPE)
        self.build_dirs()
        image_list = dataset_util.get_images_list(self.get_src_image_path())
        if len(image_list) < 1:
            print('ERROR:: no image files found in %s' % self.get_src_image_path())
            return
        image_intervals = self.get_image_intervals(image_list)
        self.copy_images(image_list, image_intervals)
        split_intervals = self.get_split_intervals(image_list)
        self.write_file_list(image_list, split_intervals)
        label_intervals = self.get_label_intervals(image_list)
        self.generate_labels(image_list, label_intervals)

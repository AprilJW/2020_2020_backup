import os
import logging
from tqdm import tqdm
import cv2
from PIL import Image
from libs.dataset_format.DatasetFormatter import DatasetFormatter
from libs.dataset_format.dataset_utilities.json_util import JsonUtil
from libs.dataset_format.dataset_utilities import dataset_util
from libs.json_io.json_parser_io import JsonParserIO


class VocFormatter(DatasetFormatter):
    FORMATTER_TYPE = dataset_util.DATASET_TYPES.VOC.name

    def __init__(self):
        super(VocFormatter, self).__init__()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        data = JsonUtil.from_file(config_path)
        self.__dict__.update(data.__dict__)

    def get_dest_mode_filename(self, mode, img_id, suffix='.jpg'):
        return self.dataset_prefix + '%06i' % img_id + suffix

    def get_voc_seg_class_path(self, img_id=-1):
        voc_seg_path = os.path.join(self.get_root_path(), 'SegmentationClass')
        if img_id == -1:
            return voc_seg_path
        else:
            sName = '%s%06i.png' % (self.dataset_prefix, img_id)
            return os.path.join(voc_seg_path, sName)

    def get_voc_seg_obj_path(self, img_id=-1):
        voc_seg_aug_path = os.path.join(self.get_root_path(), 'SegmentationClassAug')
        if img_id == -1:
            return voc_seg_aug_path
        else:
            sName = '%s%06i.png' % (self.dataset_prefix, img_id)
            return os.path.join(voc_seg_aug_path, sName)

    def get_split_types(self, split_folder):
        split_types = self.sub_dirs
        for folder_name in split_folder.split('/'):
            split_types = split_types[folder_name]
        return list(split_types.keys())

    def get_split_filepath(self, split_file_folder, split_type):
        return os.path.join(self.get_root_path(), split_file_folder, split_type)

    def get_image_intervals(self, image_list):
        images_total_num = len(image_list)
        intervals = {self.image_modes[0]: [0, images_total_num]}
        return intervals

    def get_split_intervals(self, image_list):
        images_total_num = len(image_list)
        train_num = dataset_util.get_mode_num(self.split_ids['train'], image_list)
        intervals = {'train.txt': [0, train_num],
                     'val.txt': [train_num, images_total_num],
                     'trainval.txt': [0, images_total_num]}
        return intervals

    def get_label_intervals(self, image_list):
        images_total_num = len(image_list)
        intervals = {self.label_modes[0]: [0, images_total_num],
                     self.label_modes[1]: [0, images_total_num]}
        return intervals

    def _voc_split_line_format(self, split_mode, filename):
        if split_mode == 'dataset':
            line_str = ("/%s/%s.jpg /%s/%s.png\n" % (self.image_modes[0], filename,
                                                     'SegmentationClassAug', filename)).encode()
        else:
            line_str = ("%s\n" % filename).encode()
        return line_str

    def write_file_list(self, image_list, split_intervals):
        print('writing file list ...')
        for split_mode in self.split_modes:
            split_types = self.get_split_types(split_mode)
            for split_type in split_types:
                split_file = self.get_split_filepath(split_mode, split_type)
                with open(split_file, 'wb') as file:
                    for i in range(split_intervals[split_type][0], split_intervals[split_type][1]):
                        filename, ext = os.path.splitext(image_list[i])
                        file.write(self._voc_split_line_format(split_mode, filename))

    # generate voc class segmentation images
    def _gen_mask_image_with_palette(self, img_id):
        seg_obj_path = self.get_voc_seg_obj_path(img_id)
        seg_class_path = self.get_voc_seg_class_path(img_id)
        seg_img_plt = Image.open(seg_obj_path)
        seg_img_plt.putpalette(dataset_util.color_pallete)
        seg_img_plt.save(seg_class_path)

    def _gen_seg_obj(self, img_id, label_list):
        abs_mask_file_path = self.get_src_label_filepath(img_id)
        mask_anno = JsonParserIO.from_file(abs_mask_file_path)
        image_shape = mask_anno.image_shape
        anno_objects = mask_anno.objects

        voc_area = dataset_util.get_area(image_shape, *self.get_image_size())
        seg_img, _ = dataset_util.get_masks_from_file(voc_area, anno_objects,
                                                      self.separation_linewidth, label_list)
        cv2.imwrite(self.get_voc_seg_obj_path(img_id), seg_img)

    def generate_labels(self, image_list, label_intervals):
        logging.info('generate segmentation ...')
        label_list = []
        mode = 'SegmentationClassAug'
        for srcfile in tqdm(image_list[label_intervals[mode][0]:label_intervals[mode][1]]):
            img_id = dataset_util.get_image_id(srcfile)
            self._gen_seg_obj(img_id, label_list)

        mode = 'SegmentationClass'
        for srcfile in tqdm(image_list[label_intervals[mode][0]:label_intervals[mode][1]]):
            img_id = dataset_util.get_image_id(srcfile)
            self._gen_mask_image_with_palette(img_id)

        logging.info('label list {0}'.format(label_list))
        dataset_util.write_label_id_color_file(label_list, self.paths['output'])
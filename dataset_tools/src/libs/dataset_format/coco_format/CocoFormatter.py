import os
from tqdm import tqdm
import json
import cv2
import numpy as np
from PIL import Image

from libs.dataset_format.DatasetFormatter import DatasetFormatter
from libs.dataset_format.dataset_utilities import dataset_util
from libs.dataset_format.dataset_utilities.json_util import JsonUtil
from libs.json_io.json_parser_io import JsonParserIO
from libs.image_statistics import compute_and_save_rgb_mean

def _check_identical_items(filename, item, new_item):
    if item != new_item:
        print('file %s has different annotation %s' % (filename, new_item))


class CocoFormatter(DatasetFormatter):
    FORMATTER_TYPE = dataset_util.DATASET_TYPES.COCO.name

    def __init__(self):
        super(CocoFormatter, self).__init__()
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        data = JsonUtil.from_file(config_path)
        self.__dict__.update(data.__dict__)
        self._images = {}
        self._annos = {}
        for mode in self.label_modes:
            self._images[mode] = []
            self._annos[mode] = []
        self.global_object_id = 0

    @staticmethod
    def map_mode_json2image(json_mode):
        return 'train2014' if 'train' in json_mode else 'val2014'

    def get_dest_mode_filename(self, mode, img_id, suffix='.jpg'):
        return 'COCO_' + CocoFormatter.map_mode_json2image(mode) + '_%012i' % img_id +suffix

    def get_dest_image_filepath(self, mode, img_id):
        dest_file = self.get_dest_mode_filename(mode, img_id)
        dest_path = os.path.join(self.get_dest_mode_path(mode), dest_file)
        return dest_path

    def _get_mode_json_path(self, mode, anno_type):
        json_name = anno_type + "_" + mode + '.json'
        return os.path.join(self.get_root_path(), "annotations", json_name)

    def _get_debug_seg_image_path(self, index):
        return os.path.join(self.get_debug_path(), '%06i_seg.png' % (index))

    def _get_debug_apart_seg_path(self, index):
        return os.path.join(self.get_debug_path(), '%06i_seg_apart.png' % (index))

    def _get_debug_combo_seg_path(self, index):
        return os.path.join(self.get_debug_path(), '%06i_combo.png' % (index))

    def _get_coco_url(self, mode, dest_file):
        coco_url = self.coco_base_url + CocoFormatter.map_mode_json2image(mode) + '/' + dest_file
        return coco_url

    def get_image_intervals(self, image_list):
        images_total_num = len(image_list)
        train_num = dataset_util.get_mode_num(self.split_ids['train'], image_list)
        intervals = {'train2014': [0, train_num],
                     'val2014': [train_num, images_total_num]}
        return intervals

    def get_split_intervals(self, image_list):
        return self.get_image_intervals(image_list)

    def get_label_intervals(self, image_list):
        images_total_num = len(image_list)
        train_num = dataset_util.get_mode_num(self.split_ids['train'], image_list)
        minival_num = dataset_util.get_mode_num(self.split_ids['minival'], image_list)
        intervals = {'train2014': [0, train_num],
                     'val2014': [train_num, images_total_num],
                     'minival2014': [train_num, minival_num],
                     'valminusminival2014': [minival_num, images_total_num]}
        return intervals

    def write_file_list(self, image_list, split_intervals):
        compute_and_save_rgb_mean(self.get_src_image_path(), self.get_root_path())

    def generate_labels(self, image_list, label_intervals):
        print('generate labels ...')
        self._build_image_infos(image_list, label_intervals)
        label_list, keypoints, skeleton = self._build_label_infos(image_list, label_intervals)
        info_msg, license_msg, cat_msg = self._build_fixed_msg(keypoints, skeleton, label_list)
        for mode in self.label_modes:
            json_file = open(self._get_mode_json_path(mode, self.anno_type), 'w')
            self._write_json_files(json_file, info_msg, license_msg, cat_msg, mode)

        dataset_util.write_label_id_color_file(label_list, self.get_root_path())
        print('coco format done')

    def _write_json_files(self, json_file, info_msg, license_msg, cat_msg, mode):
        json_content = {'info': info_msg,
                        'images': self._images[mode],
                        'licenses': license_msg,
                        'annotations': self._annos[mode],
                        'categories': cat_msg
                        }
        json_file.write(json.dumps(json_content))
        json_file.close()

    def _build_image_infos(self, image_list, intervals):
        for split_type in self.label_modes:
            for i in range(intervals[split_type][0], intervals[split_type][1]):
                img_id = dataset_util.get_image_id(image_list[i])
                image_msg = self._set_image_msg(img_id, split_type)
                self._images[split_type].append(image_msg)

    def _parse_single_label_file(self, img_id, mode, label_list, keypoints, skeleton):
        mask_file = self.get_src_label_filepath(img_id)
        mask_anno = JsonParserIO.from_file(mask_file)
        image_shape = mask_anno.image_shape
        anno_objects = mask_anno.objects

        if self.anno_type == 'keypoints':
            _check_identical_items(mask_file, keypoints, mask_anno.keypoints)
            _check_identical_items(mask_file, skeleton, mask_anno.skeleton)

        self._parse_annotations(mode, img_id, image_shape, anno_objects, label_list)

    def _parse_keypoints_skeleton(self, image_filename):
        keypoints, skeleton = [], []
        if self.anno_type == 'keypoints':
            img_id = dataset_util.get_image_id(image_filename)
            mask_file = self.get_src_label_filepath(img_id)
            mask_anno = JsonParserIO.from_file(mask_file)
            keypoints, skeleton = mask_anno.keypoints, mask_anno.skeleton
        return keypoints, skeleton

    def _build_label_infos(self, image_list, intervals):
        label_list = []
        keypoints, skeleton = self._parse_keypoints_skeleton(image_list[0])
        for mode in self.label_modes:
            for i in tqdm(range(intervals[mode][0], intervals[mode][1])):
                img_id = dataset_util.get_image_id(image_list[i])
                self._parse_single_label_file(img_id, mode, label_list, keypoints, skeleton)

        return label_list, keypoints, skeleton

    def _set_image_msg(self, img_id, mode):
        destfile = self.get_dest_mode_filename(mode, img_id)
        coco_url = self._get_coco_url(mode, destfile)
        width, height = self.get_image_size()

        image_msg = {"id": img_id,
                     "width": width,
                     "height": height,
                     "file_name": destfile,
                     "license": 0,
                     "coco_url": coco_url,
                     "date_captured": "2017-11-14 11:18:45"
                     }
        return image_msg

    def _set_part_obj_segmentation(self, part_cnts, part_hier, segmentation, recomb_seg_img):
        """
        append segmentation if this part of object has no more holes, otherwise keep cutting
        :param part_cnts: require length > 0
        :param part_hier: require != None
        :param segmentation:
        :param recomb_seg_img:
        :return:
        """
        assert part_hier is not None
        assert len(part_cnts) > 0
        inner_cnts_num = dataset_util.count_inner_cnts(part_hier)
        if inner_cnts_num == 0:
            for ui in range(len(part_cnts)):
                if len(part_cnts[ui]) < 5:
                    continue
                seg = part_cnts[ui][0, 0, :]
                for j in range(1, len(part_cnts[ui])):
                    seg = np.concatenate((seg, part_cnts[ui][j, 0, :]))
                segmentation.append(seg.tolist())
                cv2.drawContours(recomb_seg_img, [part_cnts[ui]], 0,
                                 (0, 0, 128), cv2.FILLED, cv2.LINE_8)
        else:
            self._set_object_segmentation_without_holes(part_cnts, part_hier, segmentation, recomb_seg_img)

    def _fill_minor_holes(self, single_seg_img, inner_cnt, segmentation, recomb_seg_img):
        cv2.drawContours(single_seg_img, [inner_cnt], 0, 255, cv2.FILLED, cv2.LINE_8)
        _, part_cnts, part_hier = cv2.findContours(single_seg_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        assert len(part_cnts) > 0
        self._set_part_obj_segmentation(part_cnts, part_hier, segmentation, recomb_seg_img)

    def _cut_through_holes(self, M, single_seg_img, segmentation, recomb_seg_img):
        assert M["m00"] > 1
        # cX = int(M["m10"] / M["m00"])
        width, height = self.get_image_size()
        cY = int(M["m01"] / M["m00"])
        startX = 0
        startY = cY
        endX = width - 1
        endY = cY

        upper_img, lower_img = dataset_util.separate_img_by_line(single_seg_img, startX, endX, startY, endY)

        _, imgUpperAlpha = cv2.threshold(upper_img, 0, 255, cv2.THRESH_BINARY)
        _, upper_cnts, upper_hier = cv2.findContours(
            imgUpperAlpha, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        _, imgLowerAlpha = cv2.threshold(lower_img, 0, 255, cv2.THRESH_BINARY)
        _, lower_cnts, lower_hier = cv2.findContours(
            imgLowerAlpha, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        if len(upper_cnts) > 0:
            self._set_part_obj_segmentation(upper_cnts, upper_hier, segmentation, recomb_seg_img)
        if len(lower_cnts) > 0:
            self._set_part_obj_segmentation(lower_cnts, lower_hier, segmentation, recomb_seg_img)

    def _set_object_segmentation_without_holes(self, obj_cnts, obj_hier, segmentation, recomb_seg_img):
        """
        cut through holes if object has inner contours
        :param obj_cnts: require length of obj_cnts > 0
        :param obj_hier: require obj_hier is not None
        :param recomb_seg_img:
        :return:
        """
        width, height = self.get_image_size()
        single_seg_img = np.zeros((height, width, 1), np.uint8)
        cv2.drawContours(single_seg_img, obj_cnts, -1, 255,
                         cv2.FILLED, cv2.LINE_8, obj_hier)

        inner_cnt = dataset_util.find_inner_cnt(obj_cnts, obj_hier)

        # this object has no inner holes, recursive loop stop here
        if inner_cnt is None:
            return

        M = cv2.moments(inner_cnt)
        if M["m00"] < 1:
            self._fill_minor_holes(single_seg_img, inner_cnt, segmentation, recomb_seg_img)
        else:
            self._cut_through_holes(M, single_seg_img, segmentation, recomb_seg_img)

    def _build_fixed_msg(self, keypoints, skeleton, label_list, license_list=['Mech-Mind License']):

        info_msg = {"date_created": "2018/01/10",
                    "contributor": "Mech-Mind",
                    "year": 2018,
                    "version": "1.0",
                    "url": "http://www.mech-mind.net/",
                    "description": "This is 1.0 version of the 2017 MS COCO dataset."
                    }

        license_msg_list = []
        for id, license in enumerate(license_list):
            license_msg = {"url": "http://www.mech-mind.net/",
                           "id": id,
                           "name": license
                           }
            license_msg_list.append(license_msg)

        cat_msg_list = []
        if self.unify_categories:
            cat_msg = {"supercategory": 'object',
                       "id": 1,
                       "name": 'object'
                       }
            cat_msg_list.append(cat_msg)
        else:
            for id, label in enumerate(label_list):
                cat_msg = {"supercategory": 'object',
                           "id": id + 1,
                           "name": label
                           }
                cat_msg_list.append(cat_msg)

        if self.anno_type == 'keypoints':
            cat_msg['keypoints'] = keypoints
            cat_msg['skeleton'] = skeleton

        return info_msg, license_msg_list, cat_msg_list

    @staticmethod
    def count_keypoints_num(keypoints):
        key_num = 0
        for i in range(int(len(keypoints) / 3)):
            if keypoints[3 * i] != 0:
                key_num += 1
        return key_num

    def _set_segmentation(self, obj_cnts, obj_hier, recomb_seg_img):
        """
        construct segmentation from cnts, hier of one object
        :param obj_cnts: requirment: length > 0
        :param obj_hier: length == 1
        :param recomb_seg_img:
        :return:
        """
        segmentation = []
        area = 0

        # object has only one outer contour
        if len(obj_cnts) == 1:
            seg = obj_cnts[0][0, 0, :]
            for j in range(1, len(obj_cnts[0])):
                seg = np.concatenate((seg, obj_cnts[0][j, 0, :]))
            segmentation.append(seg.tolist())
            cv2.drawContours(recomb_seg_img, obj_cnts, -1, (0, 0, 255), cv2.FILLED, cv2.LINE_8,
                             obj_hier)
            area = cv2.contourArea(obj_cnts[0])
        elif len(obj_cnts) > 1:
            # object has more than one contour, might have several outer contours or inner contours
            self._set_object_segmentation_without_holes(obj_cnts, obj_hier, segmentation, recomb_seg_img)
            area = 0
            for i in range(len(obj_hier[0])):
                if obj_hier[0][i][3] >= 0:
                    area -= cv2.contourArea(obj_cnts[i])
                else:
                    area += cv2.contourArea(obj_cnts[i])

        return segmentation, area

    def _set_annotation(self, mode, img_id, img_object, obj_cnts_desc,
                        bbox, recomb_seg_img, label_list):
        if len(obj_cnts_desc[0]) == 0:
            return

        segmentation, area = self._set_segmentation(obj_cnts_desc[0], obj_cnts_desc[1], recomb_seg_img)
        anno_msg = {"segmentation": segmentation,
                    "area": area,
                    "iscrowd": 0,
                    "image_id": img_id,
                    "bbox": bbox,
                    "category_id": 1 if self.unify_categories else label_list.index(obj_cnts_desc[2]) + 1,
                    "id": self.global_object_id
                    }

        if self.anno_type == 'keypoints':
            anno_msg['num_keypoints'] = CocoFormatter.count_keypoints_num(img_object.keypoints)
            anno_msg['keypoints'] = img_object.keypoints

        self._annos[mode].append(anno_msg)
        self.global_object_id += 1

    def _save_debug_seg_image(self, img_id, seg_img):
        if self.debug_status:
            seg_path = self._get_debug_seg_image_path(img_id)
            cv2.imwrite(seg_path, seg_img)
            seg_img_plt = Image.open(seg_path)
            seg_img_plt.putpalette(dataset_util.color_pallete)
            seg_img_plt.save(seg_path)

    def _save_debug_recomb_image(self, mode, img_id, final_seg_img, image_shape):
        w, h = self.get_image_size()
        if self.debug_status:
            cv2.imwrite(self._get_debug_apart_seg_path(img_id), final_seg_img)
            if mode in self.image_modes:
                origin_img_in = cv2.imread(self.get_dest_image_filepath(mode, img_id))
                img_combo = np.zeros((h, w, image_shape[2]), np.uint8)
                cv2.addWeighted(origin_img_in, 0.7, final_seg_img, 0.3, 0.0, img_combo)
                cv2.imwrite(self._get_debug_combo_seg_path(img_id), img_combo)

    def _parse_annotations(self, mode, img_id, image_shape, anno_objects, label_list):
        if anno_objects is None or len(anno_objects) == 0:
            return
        w, h = self.get_image_size()
        area = dataset_util.get_area(image_shape, w, h)
        seg_img, obj_cnts_desc_list = dataset_util.get_masks_from_file(area, anno_objects,
                                                              self.separation_linewidth,
                                                              label_list)
        self._save_debug_seg_image(img_id, seg_img)

        recomb_seg_img = np.zeros((h, w, image_shape[2]), np.uint8)
        for obj_id, img_object in enumerate(anno_objects):
            if dataset_util.is_valid_mask_anno(img_object):
                bndbox = img_object.bndbox
                coco_area = dataset_util.get_area(image_shape, w, h)
                # bndbox is on the original image, calculate the bounding box on coco image
                bbox = dataset_util.get_object_bbox(bndbox, coco_area[0], coco_area[1])
                self._set_annotation(mode, img_id, img_object, obj_cnts_desc_list[obj_id], bbox,
                                     recomb_seg_img, label_list)

        self._save_debug_recomb_image(mode, img_id, recomb_seg_img, image_shape)

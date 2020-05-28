import os
import sys
import numpy as np
import cv2
import logging

sys.path.append(os.path.abspath('../../dataset_tools/src'))
from util import img_process_util, util, item_algo
from generate_data.Item2D import Item2D

from libs.xml_io.pascal_voc_io import PascalVocReader

DIR_ATTACHMENT = "attachment"


class ImageGallery:
    def __init__(self):
        self.label_to_items = {}

    """ roi is [xmin,ymin,xmax,ymax]"""
    def clear_selected(self, selected_current_dict_key_return):
        for i in selected_current_dict_key_return:
            if i is not None:
                del self.label_to_items[i]

    def clear(self):
        self.label_to_items.clear()

    def _add_item(self, item=Item2D()):
        if item.name not in self.label_to_items.keys():
            self.label_to_items[item.name] = [item]
        else:
            self.label_to_items[item.name].append(item)

    def _load_item(self, img_path, label):
        item_image_in = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        target_item = Item2D(item_image_in)
        target_item.name = label
        target_item = item_algo.align_to(target_item)
        self._add_item(target_item)

    def _load_item_from_points(self, image, points, label, roi=None):
        mask = np.zeros([image.shape[0], image.shape[1]], np.uint8)
        points = np.array(util.float_points_to_int(points))
        cv2.drawContours(mask, [points], 0, 255, cv2.FILLED)
        contour = img_process_util.get_max_blob(mask)
        if roi is None:
            item_roi = cv2.boundingRect(contour)
        else:
            item_roi = roi

        b, g, r = cv2.split(image)
        b_roi = img_process_util.crop_image_roi(b, item_roi)
        g_roi = img_process_util.crop_image_roi(g, item_roi)
        r_roi = img_process_util.crop_image_roi(r, item_roi)
        mask_roi = img_process_util.crop_image_roi(mask, item_roi)
        item_image = cv2.merge([b_roi, g_roi, r_roi, mask_roi])
        return Item2D(item_img=item_image, name=label), item_roi

    def _load_multi_items_from_xml(self, path, file):
        objects_num = 0
        if file.endswith('.xml'):
            image = cv2.imread(os.path.join(path, os.path.splitext(file)[0] + '.jpg'))
            multi_item_xml = PascalVocReader(os.path.join(path, file))
            shapes = multi_item_xml.shapes
            parent_guid_to_idx = {}
            items = []
            rois = []
            for label, lineWidth, points, guid, parentGuid in shapes:
                if not points or len(points) <= 3:
                    logging.error(os.path.join(path, os.path.splitext(file)[0] + '.jpg') + "points is empty or less than 3")
                    continue
                if guid == parentGuid:
                    parant_item, roi = self._load_item_from_points(image=image, points=util.tuple_to_list(points),
                                                                   label=label)
                    items.append(parant_item)
                    rois.append(roi)
                    parent_guid_to_idx[parentGuid] = len(items) - 1

            for label, lineWidth, points, guid, parentGuid in shapes:
                if not points or len(points) <= 3:
                    logging.error(os.path.join(path, os.path.splitext(file)[0] + '.jpg') + "points is empty or less than 3")
                    continue
                if guid != parentGuid:
                    sub_item, _ = self._load_item_from_points(image=image, points=util.tuple_to_list(points),
                                                              label=label,
                                                              roi=rois[parent_guid_to_idx[parentGuid]])
                    items[parent_guid_to_idx[parentGuid]].sub_items.append(sub_item)
            for item in items:
                self._add_item(item)
                objects_num += 1
        return objects_num

    def load_attachments(self, objects_path):
        objects_num = 0
        sub_files = os.listdir(objects_path)
        for sub_file in sub_files:
            sub_file_path = os.path.join(objects_path, sub_file)
            if os.path.isfile(sub_file_path) and sub_file.endswith('.png'):
                label, _ = os.path.splitext(sub_file)
                self._load_item(sub_file_path, label)
                objects_num += 1
        return objects_num

    def load_multi_items(self, objects_path):
        self.clear()
        sub_file_dirs = os.listdir(objects_path)
        if DIR_ATTACHMENT in sub_file_dirs:
            sub_file_dirs.remove(DIR_ATTACHMENT)
        objects_num = 0
        for sub_file_dir in sub_file_dirs:
            sub_file_dir_path = os.path.join(objects_path, sub_file_dir)
            if os.path.isfile(sub_file_dir_path) and sub_file_dir.endswith('.png'):
                label = os.path.basename(objects_path)
                self._load_item(sub_file_dir_path, label)
                objects_num += 1
            elif os.path.isdir(sub_file_dir_path):
                objects_num += self.load_multi_items(sub_file_dir_path)
            elif os.path.isfile(sub_file_dir_path) and sub_file_dir.endswith('.xml'):
                objects_num += self._load_multi_items_from_xml(objects_path, sub_file_dir)

        return objects_num
    
    def random_load_multi_items(self, objects_path):
        self.clear()
        xml_flie_list = list(filter(lambda file : file.endswith('.xml'), os.listdir(objects_path)))
        select_file_num = np.random.randint(1, len(xml_flie_list))
        select_file_list = list(np.random.choice(xml_flie_list, select_file_num))
        objects_num = 0
        for file_item in select_file_list:
            objects_num += self._load_multi_items_from_xml(objects_path, file_item)
        return select_file_list

    def save_attachments(self, dest_path):
        attachment_path = os.path.join(dest_path, DIR_ATTACHMENT)
        os.makedirs(attachment_path, exist_ok=True)
        for label, items in self.label_to_items.items():
            for item in items:
                cv2.imwrite(os.path.join(attachment_path, '%s.png' % label), item.image)

    def save_items(self, dest_path, origin_image_paths={}):
        for label, items in self.label_to_items.items():
            objects_path = os.path.join(dest_path, label)
            os.makedirs(objects_path, exist_ok=True)
            for i, item in enumerate(items):
                if origin_image_paths:
                    cv2.imwrite(os.path.join(objects_path, '%s.png' % origin_image_paths[label][i]), item.image)
                else:
                    cv2.imwrite(os.path.join(objects_path, '%06i.png' % i), item.image)
    
    def get_max_image_shape(self):
        max_shape = 0
        for items in self.label_to_items.values():
            for item in items:
                temp_max = np.sqrt(pow(item.image.shape[0],2)+pow(item.image.shape[1],2))               
                if max_shape < temp_max:
                    max_shape = temp_max
        return max_shape                            

if __name__ == '__main__':
    src = 'D:/playground/Image/20180615_saveImgs/data_dongsheng/20180615_dongsheng/'
    test = ImageGallery()
    test._load_multi_items_from_xml(src)
    # cv2.imshow('parent',test.label_to_items['multiseedtest'][0].image)
    # cv2.waitKey(0)
    # cv2.imshow('sub',test.label_to_items['multiseedtest'][0].sub_items[0].image)
    # cv2.waitKey(0)
    # cv2.imshow('sub',test.label_to_items['multiseedtest'][0].sub_items[1].image)
    # cv2.waitKey(0)
    # test.label_to_items['multiseedtest'][0].resize(radio_height=0.5, radio_width=0.5)
    test_label = 'dongsheng_pure_box'
    test.label_to_items[test_label][0].resize(radio_width=0.3, radio_height=0.3)
    test.label_to_items[test_label][0].rotation(angle=240)

    cv2.imshow('parent1', test.label_to_items[test_label][0].image)
    cv2.waitKey(0)
    cv2.imshow('sub1', test.label_to_items[test_label][0].sub_items[0].overlap_mask_img)
    cv2.waitKey(0)
    cv2.imshow('sub1', test.label_to_items[test_label][0].sub_items[1].overlap_mask_img)
    cv2.waitKey(0)
    dst = test.label_to_items[test_label][0].sub_items[0].overlap_mask_img
    cv2.bitwise_or(test.label_to_items[test_label][0].sub_items[0].overlap_mask_img,
                   test.label_to_items[test_label][0].sub_items[1].overlap_mask_img, dst)
    cv2.imshow('rotation mask', dst)
    cv2.imwrite('resizemask.bmp', dst)
    cv2.waitKey(0)

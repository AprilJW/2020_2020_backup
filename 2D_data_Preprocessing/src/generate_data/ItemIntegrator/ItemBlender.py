import cv2
import numpy as np
import logging
from generate_data import ItemProcessor
from util import img_process_util
from util import item_algo


class ItemBlender(ItemProcessor.ItemProcessor):
    """

    """
    type = 'ItemBlender'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, image_width=1292, image_height=964, is_sharp_edge=False, exposed_area=0.7,
                 exposed_area_difficult=0.99, separation_linewidth=5, **kwargs):
        super().__init__(**kwargs)
        self.image_width = image_width
        self.image_height = image_height
        self.is_sharp_edge = is_sharp_edge
        self.exposed_area = exposed_area
        self.exposed_area_difficult = exposed_area_difficult
        self.separation_linewidth = separation_linewidth

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        #print("******", _items)
        logging.info("items")
        if _items is None:
            return [None]
        for idx, _item in enumerate(_items):
            _item = _items[idx]
            _item_upper_mask = item_algo.get_item_mask_in_origin_img(item_image=_item.image, bndbox=_item.bndbox,
                                                                     image_width=self.image_width,
                                                                     image_height=self.image_height)
            remain_area = cv2.countNonZero(_item.overlap_mask_img)
            _item.is_covered = remain_area / _item.objArea < self.exposed_area
            _item.difficult = remain_area / _item.objArea > self.exposed_area_difficult
            for sub_item in _item.sub_items:
                sub_item.is_covered = cv2.countNonZero(sub_item.overlap_mask_img) / sub_item.objArea < self.exposed_area
            if self.separation_linewidth > 0:
                _item_upper_mask_dilate = cv2.dilate(_item_upper_mask,
                                                     np.ones((self.separation_linewidth, self.separation_linewidth),
                                                             np.uint8))
            else:
                _item_upper_mask_dilate = _item_upper_mask
            for pre_idx in range(idx):
                if img_process_util.intersection(_items[pre_idx].bndbox, _item.bndbox) > 0:
                    _items[pre_idx].overlap_mask_img = item_algo.efface_covered_item(
                        item_upper_mask=_item_upper_mask_dilate,
                        item_lower=_items[pre_idx],
                        image_width=self.image_width,
                        image_height=self.image_height)
                    overlap_mask_img = item_algo.efface_covered_item(item_upper_mask=_item_upper_mask,
                                                                     item_lower=_items[pre_idx],
                                                                     image_width=self.image_width,
                                                                     image_height=self.image_height)

                    remain_area = cv2.countNonZero(overlap_mask_img)
                    _items[pre_idx].is_covered = remain_area / _items[pre_idx].objArea < self.exposed_area
                    _items[pre_idx].difficult = remain_area / _items[pre_idx].objArea > self.exposed_area_difficult
                    for sub_item in _items[pre_idx].sub_items:
                        sub_item.overlap_mask_img = item_algo.efface_covered_item(
                            item_upper_mask=_item_upper_mask_dilate,
                            item_lower=sub_item,
                            parent_bndbox=_items[pre_idx].bndbox,
                            image_width=self.image_width,
                            image_height=self.image_height)
                        sub_overlap_mask_img = item_algo.efface_covered_item(item_upper_mask=_item_upper_mask,
                                                                             item_lower=sub_item,
                                                                             parent_bndbox=_items[pre_idx].bndbox,
                                                                             image_width=self.image_width,
                                                                             image_height=self.image_height)
                        remain_area = cv2.countNonZero(sub_overlap_mask_img)
                        sub_item.is_covered = remain_area / sub_item.objArea < self.exposed_area
                        sub_item.difficult = remain_area / sub_item.objArea > self.exposed_area_difficult

        for _item in _items:
            if img_process_util.if_truncated(_item.overlap_mask_img.copy()):
                _item.is_covered = True
            else:
                _item.maskContour = img_process_util.get_max_blob(_item.overlap_mask_img.copy(), thre=128)
            if _item.is_contain_sub_items():
                for sub_item in _item.sub_items:
                    if sub_item.is_covered:
                        continue
                    if img_process_util.if_truncated(sub_item.overlap_mask_img.copy()):
                        sub_item.is_covered = True
                        continue
                    else:
                        sub_item.maskContour = img_process_util.get_max_blob(sub_item.overlap_mask_img)
                        delta_x = sub_item.bndbox[0] - _item.bndbox[0]
                        delta_y = sub_item.bndbox[1] - _item.bndbox[1]
                        sub_item.maskContour[:, :, 0] -= delta_x
                        sub_item.maskContour[:, :, 1] -= delta_y
        return [_items]


if __name__ == '__main__':
    itemblender = ItemBlender()
    itemblender.process()
    print(ItemBlender.__subclasses__())

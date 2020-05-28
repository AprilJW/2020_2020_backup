import numpy as np
import cv2
from generate_data import ItemProcessor
from util import item_algo
from util import img_process_util


class Move(ItemProcessor.ItemProcessor):
    type = 'Move'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, roi_origin_x=-1, roi_origin_y=-1, roi_w=500, roi_h=500, image_width=1292, image_height=964, **kwargs):

        super().__init__(**kwargs)
        self.roi_origin_x = roi_origin_x
        self.roi_origin_y = roi_origin_y
        self.roi_w = roi_w
        self.roi_h = roi_h
        self.image_width = image_width
        self.image_height = image_height

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)

        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None
        _target_roi = self._get_roi_from_wh_and_origin(roi_origin_x=self.roi_origin_x,
                                                        roi_origin_y=self.roi_origin_y,
                                                        roi_width=self.roi_w,
                                                        roi_height=self.roi_h,
                                                        img_width=self.image_width,
                                                        img_height=self.image_height)
        xs = np.random.randint(_target_roi[0], _target_roi[2], size=len(_items))
        ys = np.random.randint(_target_roi[1], _target_roi[3], size=len(_items))
        for idx in range(len(_items)):
            _items[idx] = item_algo.move(_items[idx], (self.image_height, self.image_width), xs[idx], ys[idx])
        return [_items]

    # (roi_origin_x, roi_origin_y) is roi top left corner coordinates
    # return roi is xmin,ymin,xmax,ymax
    def _get_roi_from_wh_and_origin(self, roi_origin_x, roi_origin_y, roi_width, roi_height, img_width, img_height):
        if roi_origin_x < 0:
            xmin, xmax = img_process_util._calculate_center_roi_min_and_max(roi_width, img_width)
        else:
            xmin, xmax = img_process_util._calculate_specific_roi_min_and_max(roi_origin_x, roi_width, img_width)
        if roi_origin_y < 0:
            ymin, ymax = img_process_util._calculate_center_roi_min_and_max(roi_height, img_height)
        else:
            ymin, ymax = img_process_util._calculate_specific_roi_min_and_max(roi_origin_y, roi_height, img_height)
        return [xmin, ymin, xmax, ymax]
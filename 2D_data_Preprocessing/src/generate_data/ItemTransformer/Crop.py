import numpy as np
import cv2
from generate_data import ItemProcessor
from util import item_algo
from util import img_process_util
from ui.property.ProcessorProperty import EnumOpts


class Crop(ItemProcessor.ItemProcessor):
    type = 'Crop'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, selected_crop_types=None, min_w=50, min_h=50, **kwargs):

        super().__init__(**kwargs)
        if selected_crop_types is None:
            selected_crop_types = list(item_algo.CropTypes.__members__.keys())[0]
        self.crop_types = EnumOpts(list(item_algo.CropTypes.__members__.keys()), selected_crop_types)

        self.min_w = min_w
        self.min_h = min_h

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)

        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None

        for _idx, _item in enumerate(_items):
            _items[_idx] = item_algo.crop(_item, self.crop_types.selected_opt, self.min_w, self.min_h)

        return [_items]

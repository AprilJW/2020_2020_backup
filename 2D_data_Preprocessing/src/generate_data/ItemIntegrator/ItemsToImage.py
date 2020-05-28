import cv2
from util import img_process_util
from generate_data.ItemProcessor import ItemProcessor


class ItemsToImage(ItemProcessor):
    type = 'ItemsToImage'
    inputs = {'items', 'background'}
    outputs = ['image']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        background = key_to_inputs['background']
        if _items is None:
            return [background]
        for item in _items:
            background[item.bndbox[1]:item.bndbox[3], item.bndbox[0]:item.bndbox[2]] = img_process_util.paint_on(
                item.image, background[item.bndbox[1]:item.bndbox[3], item.bndbox[0]:item.bndbox[2]])
        return [background]

    def __call__(self, key_to_inputs={}):
        return self.process(key_to_inputs=key_to_inputs)

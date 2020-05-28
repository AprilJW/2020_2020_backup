import numpy as np
from generate_data import ItemProcessor
from util import item_algo


class Brightness(ItemProcessor.ItemProcessor):
    type = 'Brightness'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, brightness_lower=-10, brightness_upper=10, scale=1.0, gamma_upper=1.0, gamma_lower=1.0, use_gamma=False, **kwargs):
        super().__init__(**kwargs)
        self.brightness_lower = brightness_lower
        self.brightness_upper = brightness_upper
        self.scale = scale
        self.gamma_upper = gamma_upper
        self.gamma_lower = gamma_lower
        self.use_gamma = use_gamma

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running', _items)
        if _items is None:
            return None
        for _item in _items:
            if self.use_gamma:
                gamma = np.random.uniform(self.gamma_lower, self.gamma_upper)
                _item.image = item_algo.adjust_gamma(_item.image, gamma)
            else:
                brightness = np.random.uniform(self.brightness_lower, self.brightness_upper)
                _item.image = item_algo.change_brightness(_item.image, brightness, self.scale)
        return [_items]

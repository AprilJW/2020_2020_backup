import numpy as np
from generate_data import ItemProcessor
from util import item_algo


class Resize(ItemProcessor.ItemProcessor):
    type = 'Resize'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, resize_ratio_lower=0.0, resize_ratio_upper=0.0, is_same_size_in_image=True,
                 is_same_size_in_class=False, **kwargs):
        super().__init__(**kwargs)
        """ resize ratio range in -1,inf """
        self.resize_ratio_lower = resize_ratio_lower
        self.resize_ratio_upper = resize_ratio_upper
        self.is_same_size_in_image = is_same_size_in_image
        self.is_same_size_in_class = is_same_size_in_class

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None
        resize_ratios = []
        _resize_ratio_lower = self.resize_ratio_lower + 1
        _resize_ratio_upper = self.resize_ratio_upper + 1
        if self.is_same_size_in_image:
            resize_ratios = np.zeros(len(_items)).tolist()
            resize_ratio = (_resize_ratio_upper - _resize_ratio_lower) * np.random.rand() + _resize_ratio_lower
            resize_ratios = [x + resize_ratio for x in resize_ratios]
        elif self.is_same_size_in_class:
            _item_name_to_resize_ratio = {}
            for _item in _items:
                if _item.name not in _item_name_to_resize_ratio.keys():
                    _item_name_to_resize_ratio[_item.name] = (_resize_ratio_upper - _resize_ratio_lower) * \
                                                             np.random.rand() + _resize_ratio_lower
                resize_ratios.append(_item_name_to_resize_ratio[_item.name])
        else:
            resize_ratios = (_resize_ratio_upper - _resize_ratio_lower) * np.random.rand(len(_items)) + \
                            _resize_ratio_lower
        for idx in range(len(_items)):
            _items[idx] = item_algo.resize(item=_items[idx], ratio_width=resize_ratios[idx],
                                           ratio_height=resize_ratios[idx], sigma=1.6,
                                           is_gauss_scale=False)
        return [_items]

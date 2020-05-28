from generate_data import ItemProcessor
from util import item_algo
import numpy as np


class Distortion(ItemProcessor.ItemProcessor):
    type = 'Distortion'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, grid_width=4, grid_height=4, magnitude=4, prob = 0.3, **kwargs):
        super().__init__(**kwargs)
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.magnitude = magnitude
        self.prob = prob

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None

        selected_items = []
        selected_num = int(len(_items) * self.prob)
        if selected_num > 0:
            selected_items = np.random.choice(_items, selected_num, replace=False)
        for _item in selected_items:
            _item.image = item_algo.random_distortion(_item.image, self.grid_width, self.grid_height, self.magnitude)
        return [_items]

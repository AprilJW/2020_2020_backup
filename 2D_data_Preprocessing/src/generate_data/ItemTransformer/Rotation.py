import numpy as np
from generate_data import ItemProcessor
from util import item_algo


class Rotation(ItemProcessor.ItemProcessor):
    type = 'Rotation'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, angle_lower=0.0, angle_upper=360.0,**kwargs):
        super().__init__(**kwargs)
        self.angle_lower = angle_lower
        self.angle_upper = angle_upper

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None
        rot_angles = np.random.randint(int(self.angle_lower), int(self.angle_upper), size=len(_items))
        for idx in range(len(_items)):
            _items[idx] = item_algo.rotation(_items[idx], rot_angles[idx])
        return [_items]

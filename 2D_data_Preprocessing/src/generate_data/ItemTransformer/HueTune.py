from generate_data import ItemProcessor
from util import item_algo


class HueTune(ItemProcessor.ItemProcessor):
    type = 'HueTune'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, target_hue=0.0, **kwargs):
        super().__init__(**kwargs)
        self.target_hue = target_hue

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None
        for _item in _items:
            _item.image = item_algo.change_hue(_item.image, self.target_hue)
        return [_items]

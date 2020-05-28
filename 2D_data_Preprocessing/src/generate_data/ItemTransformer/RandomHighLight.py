from generate_data import ItemProcessor
from util import item_algo


class RandomHighLight(ItemProcessor.ItemProcessor):
    type = 'RandomHighLight'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, min_hl_num=0, max_hl_num=10, min_hl_area=100, max_hl_area=1000, **kwargs):
        super().__init__(**kwargs)
        self.min_hl_num = min_hl_num
        self.max_hl_num = max_hl_num
        self.min_hl_area = min_hl_area
        self.max_hl_area = max_hl_area

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None
        for _item in _items:
            _item.image = item_algo.random_highlight(_item.image, self.min_hl_num, self.max_hl_num, self.min_hl_area,
                                                     self.max_hl_area)
        return [_items]

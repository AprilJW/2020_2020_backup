from generate_data import ItemProcessor
from util import item_algo


class Contrast(ItemProcessor.ItemProcessor):
    type = 'Contrast'
    inputs = {'items'}
    outputs = ['items']

    def __init__(self, clip_limit=4.0, tile_grid_size_w=8, tile_grid_size_h=8, **kwargs):
        super().__init__(**kwargs)
        self.clip_limit = clip_limit
        self.tile_grid_size_w = tile_grid_size_w
        self.tile_grid_size_h = tile_grid_size_h

    def process(self, key_to_inputs={}):
        if not super()._check_input_is_satisfied(input_keys=self.inputs, key_to_inputs=key_to_inputs):
            raise TypeError('input not satisfied in ', self.type)
        _items = key_to_inputs['items']
        print(self.type, 'running')
        if _items is None:
            return None
        for _item in _items:
            _item.image = item_algo.change_contrast(_item.image, self.clip_limit,
                                                    (self.tile_grid_size_w, self.tile_grid_size_h))
        return [_items]
